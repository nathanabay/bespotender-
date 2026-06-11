import frappe
from pypdf import PdfReader, PdfWriter
from io import BytesIO
import tempfile
import os
import subprocess

def append_document(writer, file_doc, get_pdf_with_letterhead):
    """
    Appends a document to the PdfWriter. Handles PDF and DOCX/DOC conversion.
    """
    file_content = file_doc.get_content()
    file_name = file_doc.file_name.strip() # Use strip to remove leading/trailing whitespace

    if file_name.lower().endswith(".pdf"):
        try:
            writer.append_pages_from_reader(PdfReader(BytesIO(file_content)))
        except Exception as e:
            frappe.log_error(message=f"Failed to append PDF {file_name}: {e}", title="PDF Append Failed")
            msg_body = f"<div style='padding: 50px; text-align: center;'><p>Could not append PDF: {file_name}</p></div>"
            writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(msg_body))))
    
    elif file_name.lower().endswith((".docx", ".doc")):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Sanitize filename to prevent path traversal attacks
            safe_file_name = os.path.basename(file_name.strip())
            original_filename = os.path.splitext(safe_file_name)[0]
            doc_path = os.path.join(temp_dir, safe_file_name)
            pdf_path = os.path.join(temp_dir, f"{original_filename}.pdf")

            with open(doc_path, "wb") as f:
                f.write(file_content)

            try:
                # Run unoconv to convert the document to pdf
                # timeout=120 prevents indefinitely blocking a worker thread
                subprocess.run(
                    ["unoconv", "-f", "pdf", "-o", pdf_path, doc_path],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                with open(pdf_path, "rb") as f:
                    pdf_content = f.read()
                
                writer.append_pages_from_reader(PdfReader(BytesIO(pdf_content)))

            except FileNotFoundError:
                error_message = f"Failed to convert Word document: {file_name}. The 'unoconv' command was not found. Please ensure it is installed on your server (e.g., 'sudo apt-get install unoconv')."
                frappe.log_error(message=error_message, title="DOCX Conversion Failed: Command Not Found")
                msg_body = f"<div style='padding: 50px; text-align: center;'><p style='color: red;'><b>Conversion Failed</b></p><p>Could not convert file: <b>{file_name}</b></p><p style='font-size: 10px; color: grey;'>Reason: `unoconv` is not installed.</p></div>"
                writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(msg_body))))
            except subprocess.CalledProcessError as e:
                error_message = f"Failed to convert Word document: {file_name}. `unoconv` failed. STDERR: {e.stderr}"
                frappe.log_error(message=error_message, title="DOCX Conversion Failed: unoconv Error")
                msg_body = f"<div style='padding: 50px; text-align: center;'><p style='color: red;'><b>Conversion Failed</b></p><p>Could not convert file: <b>{file_name}</b></p><p style='font-size: 10px; color: grey;'>Reason: {e.stderr}</p></div>"
                writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(msg_body))))
    
    else:
        msg_body = f"<div style='padding: 50px; text-align: center;'><p>Unsupported file type for compilation: {file_name}</p></div>"
        writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(msg_body))))

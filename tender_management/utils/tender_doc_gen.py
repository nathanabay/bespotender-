import frappe
import re
from frappe.utils.pdf import get_pdf
import frappe.utils
import time
import random
import string
from pypdf import PdfReader, PdfWriter
from io import BytesIO

@frappe.whitelist()
def generate_proposal_document(template_name, tender_name):
    # No docstring here to shift line numbers
    template = frappe.get_doc("Document Template", template_name)
    tender = frappe.get_doc("Tender Opportunity", tender_name)
    content = template.content or ""
    placeholders = {
        "tender_title": tender.title or "",
        "client": tender.client or "",
        "organization": tender.client or "",
        "tender_number": tender.tender_number or "",
        "submission_deadline": str(tender.submission_deadline) if tender.submission_deadline else "",
        "final_bid_price": str(tender.final_bid_price) if tender.final_bid_price else "",
        "sector": tender.sector or "",
        "tender_type": tender.tender_type or "",
        "company_name": frappe.defaults.get_defaults().get("company") or "BES"
    }
    for key, value in placeholders.items():
        content = re.sub(r'\{\{' + key + r'\}\}', str(value), content, flags=re.IGNORECASE)
        content = re.sub(r'\{' + key + r'\}', str(value), content, flags=re.IGNORECASE)
    return content

@frappe.whitelist()
def download_pdf(html, tender_name, template_name, filename="document.pdf"):
    # No docstring here to shift line numbers
    if not frappe.has_permission("Tender Opportunity", "write", doc=tender_name):
        frappe.throw(frappe._("Not permitted to generate documents for this Tender Opportunity"), frappe.PermissionError)
    pdf_content = get_pdf(html)
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": filename,
        "attached_to_doctype": "Tender Opportunity",
        "attached_to_name": tender_name,
        "content": pdf_content,
        "is_private": 1
    })
    file_doc.insert()
    try:
        tender = frappe.get_doc("Tender Opportunity", tender_name)
        tender.append("generated_documents", {
            "template": template_name,
            "file": file_doc.file_url,
            "generated_by": frappe.session.user,
            "date": frappe.utils.now_datetime()
        })
        tender.save()
    except Exception as e:
        frappe.log_error(f"Failed to link generated document: {str(e)}", "Document Generation")
    frappe.response.filename = filename
    frappe.response.filecontent = pdf_content
    frappe.response.type = "download"

def extract_financial_document(doc, method):
    try:
        if doc.quotation_ref:
            files = frappe.get_all("File", filters={
                "attached_to_doctype": "Quotation",
                "attached_to_name": doc.quotation_ref
            }, fields=["file_url"], order_by="creation desc", limit=1)
            if files:
                doc.extracted_financial_document = files[0].file_url
    except Exception as e:
        frappe.log_error(f"Failed to extract financial document: {str(e)}", "Financial Extraction Hook")

@frappe.whitelist()
def generate_compiled_tender_document_v5(tender_name):
    frappe.msgprint("Starting Compiled Bid Generation v5...")
    
    tender = frappe.get_doc("Tender Opportunity", tender_name)
    bid_mgmt = frappe.get_single("Bid Document Management")
    
    # Robust Cleanup
    try:
        old_entries = frappe.get_all("Tender Generated Document", 
            filters={"parent": tender.name, "template": "Compiled Bid"},
            fields=["file", "name"]
        )
        for entry in old_entries:
            if entry.file:
                clean_url = entry.file.split('?')[0]
                file_doc_name = frappe.db.get_value("File", {"file_url": clean_url}, "name")
                if file_doc_name:
                    frappe.delete_doc("File", file_doc_name, ignore_permissions=True)
            frappe.db.delete("Tender Generated Document", {"name": entry.name})
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Cleanup failed: {str(e)}", "Compiled Bid Cleanup")

    header_html = """
    <div class="letterhead-header" style="overflow: hidden; margin-bottom: 10px;">
      <table style="width: 100%; border-collapse: collapse;">
        <tr>
          <td style="width: 55%; vertical-align: bottom; text-align: left; padding-bottom: 5px;">
            <img src="https://erp.bespo.et/files/bespo%20new%20.png" style="max-height: 60px; width: auto; margin-bottom: 8px; display: block;" alt="Bespo Logo">
            <h1 style="margin: 0; font-size: 18px; color: #333132; font-weight: 800; line-height: 1.1;">
              BESPO <span style="color: #d92027;">ELECTRO MECHANICAL</span><br>SERVICES PLC
            </h1>
            <p style="margin: 3px 0 0; font-size: 9px; color: #666; letter-spacing: 2px; text-transform: uppercase; font-weight: bold;">
              The Power People
            </p>
          </td>
          <td style="width: 45%; vertical-align: bottom; text-align: right; padding-bottom: 5px;">
            <div style="margin-bottom: 5px;">
              <strong style="color: #d92027; font-size: 9px; display: block; margin-bottom: 1px;">TEL / FAX</strong>
              <span style="color: #333132; font-size: 10px;">+251 11 629 9030 / 31</span><br>
              <span style="color: #333132; font-size: 10px;">Fax: +251 116 298999</span>
            </div>
          </td>
        </tr>
      </table>
    </div>
    <div style="width: 100%; height: 2px; clear: both; margin-bottom: 15px;">
        <div style="float: left; width: 55%; height: 2px; background-color: #333132;"></div>
        <div style="float: left; width: 45%; height: 2px; background-color: #d92027;"></div>
    </div>
    """
    
    letter_head_db = frappe.db.get_value("Letter Head", {"is_default": 1}, "footer")
    footer_html = letter_head_db if letter_head_db else ""

    def get_pdf_with_letterhead(html_body):
        full_html = f"""
        <html>
        <head>
            <style>
                @page {{ margin: 5mm; }}
                body {{ font-family: 'Helvetica', 'Arial', sans-serif; margin: 0; padding: 0; font-size: 11pt; line-height: 1.3; }}
                .letter-head {{ width: 100%; margin: 0; padding: 0; }}
                .letter-footer {{ width: 100%; margin: 0; padding: 0; }}
                .content-wrapper {{ padding: 10px 30px; margin: 0; }}
                h1, h2, h3 {{ font-family: 'Helvetica', 'Arial', sans-serif; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <div class="letter-head">{header_html}</div>
            <div class="content-wrapper">{html_body}</div>
            <div class="letter-footer">{footer_html}</div>
        </body>
        </html>
        """
        return get_pdf(full_html)

    def append_document_to_writer(writer, file_doc, get_pdf_with_letterhead):
        import tempfile
        import os
        import subprocess

        file_content = file_doc.get_content()
        file_name = file_doc.file_name

        if file_name.lower().endswith(".pdf"):
            writer.append_pages_from_reader(PdfReader(BytesIO(file_content)))
        
        elif file_name.lower().endswith((".docx", ".doc")):
            with tempfile.TemporaryDirectory() as temp_dir:
                original_filename = os.path.splitext(file_name)[0]
                doc_path = os.path.join(temp_dir, file_name)
                pdf_path = os.path.join(temp_dir, f"{original_filename}.pdf")

                with open(doc_path, "wb") as f:
                    f.write(file_content)

                try:
                    # Run unoconv to convert docx to pdf
                    result = subprocess.run(
                        ["unoconv", "-f", "pdf", "-o", pdf_path, doc_path],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    
                    with open(pdf_path, "rb") as f:
                        pdf_content = f.read()
                    
                    writer.append_pages_from_reader(PdfReader(BytesIO(pdf_content)))

                except FileNotFoundError:
                    error_message = f"Failed to convert Word document: {file_name}. The 'unoconv' command was not found. Please install it on your server (e.g., 'sudo apt-get install unoconv')."
                    frappe.log_error(message=error_message, title="DOCX Conversion Failed: Command Not Found")
                    msg_body = f"<div style='padding: 50px; text-align: center;'><p style='color: red;'><b>Conversion Failed</b></p><p>Could not convert file: <b>{file_name}</b></p><p style='font-size: 10px; color: grey;'>Reason: `unoconv` is not installed on the server.</p></div>"
                    writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(msg_body))))
                except subprocess.CalledProcessError as e:
                    error_message = f"Failed to convert Word document: {file_name}. `unoconv` command failed with exit code {e.returncode}. STDERR: {e.stderr}"
                    frappe.log_error(message=error_message, title="DOCX Conversion Failed: unoconv Error")
                    msg_body = f"<div style='padding: 50px; text-align: center;'><p style='color: red;'><b>Conversion Failed</b></p><p>Could not convert file: <b>{file_name}</b></p><p style='font-size: 10px; color: grey;'>Reason: {e.stderr}</p></div>"
                    writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(msg_body))))
        
        else:
            msg_body = f"<div style='padding: 50px; text-align: center;'><p>Unsupported file type: {file_name}</p></div>"
            writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(msg_body))))


    writer = PdfWriter()
    
    cover_body = f"""
        <div style="text-align: center; padding-top: 150px; padding-bottom: 50px;">
            <h1 style="color: #333132; font-size: 32px; margin-bottom: 10px; text-transform: uppercase; font-weight: 800;">Compiled Bid Document</h1>
            <div style="width: 120px; height: 4px; background-color: #d92027; margin: 20px auto 40px auto;"></div>
            <h2 style="color: #333132; font-size: 24px; margin-bottom: 60px; font-weight: normal; letter-spacing: 1px;">{tender.title}</h2>
            <div style="display: inline-block; text-align: left; background-color: #f9f9f9; padding: 30px; border-radius: 8px; border: 1px solid #eee;">
                <table style="font-size: 14px; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 20px; color: #666; text-transform: uppercase; font-size: 10px; letter-spacing: 1px;">Tender Number</td>
                        <td style="padding: 8px 20px; font-weight: bold; color: #333;">{tender.tender_number or 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 20px; color: #666; text-transform: uppercase; font-size: 10px; letter-spacing: 1px;">Client</td>
                        <td style="padding: 8px 20px; font-weight: bold; color: #333;">{tender.client or 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 20px; color: #666; text-transform: uppercase; font-size: 10px; letter-spacing: 1px;">Sector</td>
                        <td style="padding: 8px 20px; font-weight: bold; color: #333;">{tender.sector or 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 20px; color: #666; text-transform: uppercase; font-size: 10px; letter-spacing: 1px;">Generated Date</td>
                        <td style="padding: 8px 20px; font-weight: bold; color: #333;">{frappe.utils.format_datetime(frappe.utils.now_datetime())}</td>
                    </tr>
                </table>
            </div>
        </div>
    """
    writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(cover_body))))
    
    try:
        if frappe.db.exists("Document Template", "Technical Proposal Cover Letter"):
            cover_letter_doc = frappe.get_doc("Document Template", "Technical Proposal Cover Letter")
            if cover_letter_doc.content:
                context = tender.as_dict()
                context.update({
                    "company_name": "BESPO ELECTRO MECHANICAL SERVICES PLC",
                    "organization": tender.client or "Valued Client",
                    "tender_title": tender.title or "N/A",
                    "submission_deadline": frappe.utils.formatdate(tender.submission_deadline) if tender.get("submission_deadline") else "N/A",
                    "tender_number": tender.tender_number or "N/A"
                })
                rendered_html = frappe.render_template(cover_letter_doc.content, context)
                writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(rendered_html))))
    except Exception as e:
        frappe.log_error(f"Technical Proposal Cover Letter failed: {str(e)}", "Document Compilation")

    sections = [
        {"title": "1. Legal & Administrative", "table": "legal_and_administrative_documents"},
        {"title": "2. Our Company Profile", "table": "company_profile_documents"},
        {"title": "3. Our Employee List and CV", "table": "employee_list_cv_documents"},
        {"title": "4. Bid Submission Sheets", "file": tender.bid_submission_sheets},
        {"title": "5. Technical Methodology", "file": tender.technical_methodology},
        {"title": "6. Manufacturer Authorization Form (MAF)", "file": tender.manufacturer_authorization_form},
        {"title": "7. Supplier Company Profile & Certifications", "table": "supplier_company_profile"},
        {"title": "8. The Bid Document", "file": tender.the_bid_document},
        {"title": "9. Financial Document", "file": tender.extracted_financial_document}
    ]
    
    for section in sections:
        # Determine the source of documents: either the main tender doc or the Bid Document Management singleton
        doc_source = bid_mgmt if section.get("table") in ["legal_and_administrative_documents", "company_profile_documents", "employee_list_cv_documents", "supplier_company_profile"] else tender

        if "table" in section:
            table_name = section["table"]
            rows = doc_source.get(table_name) or []
            if rows:
                main_sep_body = f"<div style='padding-top: 400px; text-align: center;'><h1>{section['title']}</h1></div>"
                writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(main_sep_body))))
                for row in rows:
                    if row.file:
                        try:
                            file_doc = frappe.get_doc("File", {"file_url": row.file})
                            append_document_to_writer(writer, file_doc, get_pdf_with_letterhead)
                        except Exception as e:
                            frappe.log_error(f"Table row failure for {row.file}: {str(e)}", "Document Compilation")
            continue

        if section.get('file'):
            file_url = section['file']
            if file_url:
                try:
                    file_doc = frappe.get_doc("File", {"file_url": file_url})
                    sep_body = f"<div style='padding-top: 400px; text-align: center;'><h1>{section['title']}</h1></div>"
                    writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(sep_body))))
                    append_document_to_writer(writer, file_doc, get_pdf_with_letterhead)
                except Exception as e:
                    frappe.log_error(f"File section failure for {file_url}: {str(e)}", "Document Compilation")

    output_stream = BytesIO()
    writer.write(output_stream)
    pdf_content = output_stream.getvalue()
    
    rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    timestamp = int(time.time())
    filename = f"{tender.name}_Compiled_Bid_{timestamp}_{rand_str}.pdf"
    
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": filename,
        "attached_to_doctype": "Tender Opportunity",
        "attached_to_name": tender.name,
        "content": pdf_content,
        "is_private": 1
    })
    file_doc.insert(ignore_permissions=True)
    
    tender.reload()
    tender.append("generated_documents", {
        "template": "Compiled Bid",
        "file": file_doc.file_url,
        "generated_by": frappe.session.user,
        "date": frappe.utils.now_datetime()
    })
    tender.save(ignore_permissions=True)
    
    return f"{file_doc.file_url}?v={timestamp}"

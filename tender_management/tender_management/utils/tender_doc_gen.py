import frappe
import re
from frappe.utils.pdf import get_pdf
import frappe.utils

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
            # Find files attached to the Quotation
            files = frappe.get_all("File", filters={
                "attached_to_doctype": "Quotation",
                "attached_to_name": doc.quotation_ref
            }, fields=["file_url"], order_by="creation desc", limit=1)
            
            if files:
                doc.extracted_financial_document = files[0].file_url
    except Exception as e:
        frappe.log_error(f"Failed to extract financial document: {str(e)}", "Financial Extraction Hook")

@frappe.whitelist()
def generate_compiled_tender_document(tender_name):
    from pypdf import PdfReader, PdfWriter
    from io import BytesIO
    
    tender = frappe.get_doc("Tender Opportunity", tender_name)
    bid_mgmt = frappe.get_single("Bid Document Management")
    
    writer = PdfWriter()
    
    # 1. Create and Add Cover Page
    cover_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; padding: 100px 50px; text-align: center; }}
            h1 {{ color: #2c3e50; font-size: 32px; margin-bottom: 20px; }}
            h2 {{ color: #7f8c8d; font-size: 24px; margin-bottom: 50px; }}
            .info {{ margin-top: 50px; font-size: 18px; line-height: 1.6; }}
            .footer {{ position: fixed; bottom: 50px; width: 100%; text-align: center; color: #bdc3c7; }}
        </style>
    </head>
    <body>
        <h1>Compiled Technical Bid Package</h1>
        <h2>{tender.title}</h2>
        
        <div class="info">
            <p><strong>Tender Number:</strong> {tender.tender_number or 'N/A'}</p>
            <p><strong>Client:</strong> {tender.client or 'N/A'}</p>
            <p><strong>Sector:</strong> {tender.sector or 'N/A'}</p>
            <p><strong>Generated Date:</strong> {frappe.utils.format_datetime(frappe.utils.now_datetime())}</p>
        </div>
        
        <div class="footer">
            Generated via Tender Management System
        </div>
    </body>
    </html>
    """
    cover_pdf_content = get_pdf(cover_html)
    writer.append_pages_from_reader(PdfReader(BytesIO(cover_pdf_content)))
    
    # 2. Add sections
    sections = [
        {"title": "1. Legal & Administrative", "file": bid_mgmt.legal_and_administrative},
        {"title": "2. Our Company Profile", "file": bid_mgmt.our_company_profile},
        {"title": "3. Our Employee List and CV", "file": bid_mgmt.our_employee_list_and_cv},
        {"title": "4. Bid Submission Sheets", "file": tender.bid_submission_sheets},
        {"title": "5. Technical Methodology", "file": tender.technical_methodology},
        {"title": "6. Supplier Company Profile", "file": tender.supplier_company_profile},
        {"title": "7. Supplier ISO and Other Certification", "file": tender.supplier_iso_certification},
        {"title": "8. The Bid Document", "file": tender.the_bid_document},
        {"title": "9. Financial Document", "file": tender.extracted_financial_document}
    ]
    
    for section in sections:
        if section['file']:
            try:
                # Find File document to get content
                file_name_in_db = frappe.db.get_value("File", {"file_url": section['file']}, "name")
                if not file_name_in_db:
                    # Try private path
                    file_name_in_db = frappe.db.get_value("File", {"file_url": section['file']}, "name")
                
                if file_name_in_db:
                    file_doc = frappe.get_doc("File", file_name_in_db)
                    file_content = file_doc.get_content()
                    
                    if section['file'].lower().endswith(".pdf"):
                        # Add a separator/title page for the section
                        sep_html = f"<div style='padding-top: 300px; text-align: center; font-family: sans-serif;'><h1>{section['title']}</h1></div>"
                        sep_pdf = get_pdf(sep_html)
                        writer.append_pages_from_reader(PdfReader(BytesIO(sep_pdf)))
                        
                        # Append the actual PDF content
                        section_reader = PdfReader(BytesIO(file_content))
                        writer.append_pages_from_reader(section_reader)
                    else:
                        # For non-PDF files, add a page with a link/note
                        msg_html = f"""
                        <div style='padding: 100px; font-family: sans-serif; text-align: center;'>
                            <h1>{section['title']}</h1>
                            <p>This section contains a non-PDF file: <b>{file_doc.file_name}</b></p>
                            <p>Please access it separately via the Tender Opportunity record.</p>
                        </div>
                        """
                        msg_pdf = get_pdf(msg_html)
                        writer.append_pages_from_reader(PdfReader(BytesIO(msg_pdf)))
            except Exception as e:
                frappe.log_error(f"Failed to include section {section['title']}: {str(e)}", "Document Compilation")
        else:
            # Missing file placeholder
            msg_html = f"<div style='padding: 100px; font-family: sans-serif; text-align: center; color: red;'><h1>{section['title']}</h1><p>No document attached for this section.</p></div>"
            msg_pdf = get_pdf(msg_html)
            writer.append_pages_from_reader(PdfReader(BytesIO(msg_pdf)))
            
    # 3. Finalize and Save
    output_stream = BytesIO()
    writer.write(output_stream)
    pdf_content = output_stream.getvalue()
    
    filename = f"{tender.name}_Compiled_Bid.pdf"
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": filename,
        "attached_to_doctype": "Tender Opportunity",
        "attached_to_name": tender_name,
        "content": pdf_content,
        "is_private": 1
    })
    file_doc.insert()
    
    # Track in child table
    if not hasattr(tender, "generated_documents"):
        tender.load_from_db()

    if not frappe.db.exists("Document Template", "Compiled Bid"):
        frappe.get_doc({
            "doctype": "Document Template",
            "template_name": "Compiled Bid",
            "doc_type": "Others",
            "category": "Technical Proposal",
            "is_active": 1,
            "content": "Compiled Bid Package"
        }).insert(ignore_permissions=True)

    tender.append("generated_documents", {
        "template": "Compiled Bid",
        "file": file_doc.file_url,
        "generated_by": frappe.session.user,
        "date": frappe.utils.now_datetime()
    })
    tender.save()
    
    return file_doc.file_url


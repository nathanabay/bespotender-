import frappe
import re
from frappe.utils.pdf import get_pdf

@frappe.whitelist()
def generate_proposal_document(template_name, tender_name):
    """
    Standalone whitelisted function to generate document content from template.
    Separated from the DocType class to avoid naming collisions.
    """
    template = frappe.get_doc("Document Template", template_name)
    tender = frappe.get_doc("Tender Opportunity", tender_name)
    
    content = template.content or ""
    
    # Define placeholder mapping
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
    
    # Replace placeholders
    for key, value in placeholders.items():
        content = re.sub(r'\{\{' + key + r'\}\}', value, content, flags=re.IGNORECASE)
        content = re.sub(r'\{' + key + r'\}', value, content, flags=re.IGNORECASE)
    
    return content

@frappe.whitelist()
def download_pdf(html, tender_name, template_name, filename="document.pdf"):
    """
    Generate and download PDF from HTML content and link it to the tender.
    Separated from the DocType class to avoid naming collisions.
    """
    if not frappe.has_permission("Tender Opportunity", "write", doc=tender_name):
        frappe.throw(frappe._("Not permitted to generate documents for this Tender Opportunity"), frappe.PermissionError)

    pdf_content = get_pdf(html)
    
    # Save to File DocType
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": filename,
        "attached_to_doctype": "Tender Opportunity",
        "attached_to_name": tender_name,
        "content": pdf_content,
        "is_private": 1
    })
    file_doc.insert()
    
    # Add to Tender Opportunity child table
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

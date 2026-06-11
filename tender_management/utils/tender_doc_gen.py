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
    if not frappe.has_permission("Tender Opportunity", "read", doc=tender_name):
        frappe.throw(frappe._("Not permitted to view this Tender Opportunity"), frappe.PermissionError)
    if not frappe.has_permission("Document Template", "read", doc=template_name):
        frappe.throw(frappe._("Not permitted to view this Document Template"), frappe.PermissionError)
        
    template = frappe.get_doc("Document Template", template_name)
    tender = frappe.get_doc("Tender Opportunity", tender_name)
    content = template.content or ""
    placeholders = {
        "tender_title": tender.title or "",
        "client": tender.client or "",
        "organization": tender.client or "",
        "tender_number": tender.tender_number or "",
        "submission_deadline": str(tender.submission_deadline) if tender.submission_deadline else "",
        "final_bid_price": frappe.utils.fmt_money(tender.final_bid_price) if tender.final_bid_price else "",
        "sector": tender.sector or "",
        "tender_type": tender.tender_type or "",
        "company_name": frappe.defaults.get_defaults().get("company") or "BES"
    }
    safe_content = frappe.utils.sanitize_html(content)
    return frappe.render_template(safe_content, placeholders)


@frappe.whitelist()
def download_pdf(html, tender_name, template_name, filename="document.pdf"):
    if not frappe.has_permission("Tender Opportunity", "write", doc=tender_name):
        frappe.throw(frappe._("Not permitted to generate documents for this Tender Opportunity"), frappe.PermissionError)
    if not frappe.has_permission("Document Template", "read", doc=template_name):
        frappe.throw(frappe._("Not permitted to access this Document Template"), frappe.PermissionError)
        
    filename = frappe.utils.escape_html(filename)
    safe_html = frappe.utils.sanitize_html(html)
    pdf_content = get_pdf(safe_html)
    
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
    if not frappe.has_permission("Tender Opportunity", "write", doc=tender_name):
        frappe.throw(frappe._("Not permitted to compile documents for this Tender Opportunity"), frappe.PermissionError)
        
    frappe.enqueue(
        "tender_management.utils.tender_doc_gen.run_generate_compiled_tender_document_v5",
        queue="long",
        timeout=1500,
        tender_name=tender_name
    )
    return frappe._("Document generation has been queued in the background. It will appear in the Generated Documents table once finished.")

def get_pdf_with_letterhead(html_body, header_html, footer_html):
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
    safe_html = frappe.utils.sanitize_html(full_html)
    return get_pdf(safe_html)

def run_generate_compiled_tender_document_v5(tender_name):
    if not frappe.has_permission("Tender Opportunity", "write", doc=tender_name):
        return

    frappe.msgprint("Starting Compiled Bid Generation v5...")
    tender = frappe.get_doc("Tender Opportunity", tender_name)
    bid_mgmt = frappe.get_single("Bid Document Management")
    
    # Robust Cleanup
    try:
        old_entries = frappe.get_all("Tender Generated Document", 
            filters={"parent": tender.name, "template": "Compiled Bid"},
            fields=["file", "name"]
        )
        
        file_urls = [entry.file.split('?')[0] for entry in old_entries if entry.file]
        if file_urls:
            file_docs = frappe.get_all("File", filters={"file_url": ("in", file_urls)}, pluck="name")
            for file_name in file_docs:
                frappe.delete_doc("File", file_name)
        
        entry_names = [entry.name for entry in old_entries]
        if entry_names:
            frappe.db.delete("Tender Generated Document", {"name": ("in", entry_names)})
            
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

    writer = PdfWriter()
    
    cover_body = f"""
        <div style="text-align: center; padding-top: 150px; padding-bottom: 50px;">
            <h1 style="color: #333132; font-size: 32px; margin-bottom: 10px; text-transform: uppercase; font-weight: 800;">Compiled Bid Document</h1>
            <div style="width: 120px; height: 4px; background-color: #d92027; margin: 20px auto 40px auto;"></div>
            <h2 style="color: #333132; font-size: 24px; margin-bottom: 60px; font-weight: normal; letter-spacing: 1px;">{frappe.utils.escape_html(tender.title or "")}</h2>
            <div style="display: inline-block; text-align: left; background-color: #f9f9f9; padding: 30px; border-radius: 8px; border: 1px solid #eee;">
                <table style="font-size: 14px; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 20px; color: #666; text-transform: uppercase; font-size: 10px; letter-spacing: 1px;">Tender Number</td>
                        <td style="padding: 8px 20px; font-weight: bold; color: #333;">{frappe.utils.escape_html(tender.tender_number or 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 20px; color: #666; text-transform: uppercase; font-size: 10px; letter-spacing: 1px;">Client</td>
                        <td style="padding: 8px 20px; font-weight: bold; color: #333;">{frappe.utils.escape_html(tender.client or 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 20px; color: #666; text-transform: uppercase; font-size: 10px; letter-spacing: 1px;">Sector</td>
                        <td style="padding: 8px 20px; font-weight: bold; color: #333;">{frappe.utils.escape_html(tender.sector or 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 20px; color: #666; text-transform: uppercase; font-size: 10px; letter-spacing: 1px;">Generated Date</td>
                        <td style="padding: 8px 20px; font-weight: bold; color: #333;">{frappe.utils.escape_html(frappe.utils.format_datetime(frappe.utils.now_datetime()))}</td>
                    </tr>
                </table>
            </div>
        </div>
    """
    writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(cover_body, header_html, footer_html))))
    
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
                safe_content = frappe.utils.sanitize_html(cover_letter_doc.content)
                rendered_html = frappe.render_template(safe_content, context)
                writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(rendered_html, header_html, footer_html))))
    except Exception as e:
        frappe.log_error(f"Technical Proposal Cover Letter failed: {str(e)}", "Document Compilation")

    sections = [
        {"title": "1. Legal & Administrative", "table": "legal_and_administrative_documents"},
        {"title": "2. Our Company Profile", "table": "company_profile_documents"},
        {"title": "3. Our Employee List and CV", "table": "employee_list_cv_documents"},
        {"title": "4. Bid Submission Sheets", "table": "bid_submission_sheets"},
        {"title": "5. Technical Methodology", "file": tender.technical_methodology},
        {"title": "6. Manufacturer Authorization Form (MAF)", "file": tender.manufacturer_authorization_form},
        {"title": "7. Supplier Company Profile & Certifications", "table": "supplier_company_profile"},
        {"title": "8. The Bid Document", "file": tender.the_bid_document},
        {"title": "9. Financial Document", "file": tender.extracted_financial_document}
    ]
    
    # Pre-fetch files to fix N+1 issue
    file_urls = []
    for section in sections:
        doc_source = bid_mgmt if section.get("table") in ["legal_and_administrative_documents", "company_profile_documents", "employee_list_cv_documents"] else tender
        if "table" in section:
            rows = doc_source.get(section["table"]) or []
            for row in rows:
                if row.file:
                    file_urls.append(row.converted_pdf or row.file)
        elif section.get('file'):
            file_urls.append(section['file'])

    file_docs_map = {}
    if file_urls:
        file_records = frappe.get_all("File", filters={"file_url": ("in", file_urls)}, fields=["name", "file_name", "file_url"])
        for rec in file_records:
            file_docs_map[rec.file_url] = rec.name

    for section in sections:
        doc_source = bid_mgmt if section.get("table") in ["legal_and_administrative_documents", "company_profile_documents", "employee_list_cv_documents"] else tender

        if "table" in section:
            rows = doc_source.get(section["table"]) or []
            if rows:
                main_sep_body = f"<div style='padding-top: 400px; text-align: center;'><h1>{frappe.utils.escape_html(section['title'])}</h1></div>"
                writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(main_sep_body, header_html, footer_html))))
                for row in rows:
                    if row.file:
                        try:
                            file_to_use = row.converted_pdf or row.file
                            file_name = file_docs_map.get(file_to_use)
                            if not file_name:
                                continue
                            file_doc = frappe.get_doc("File", file_name)

                            if file_doc.file_name.lower().endswith('.pdf'):
                                writer.append_pages_from_reader(PdfReader(BytesIO(file_doc.get_content())))
                            else:
                                msg_body = f"<div style='padding: 50px; text-align: center;'><p style='color:orange;'><b>File Not Ready or Unsupported</b></p><p>File '{frappe.utils.escape_html(file_doc.file_name)}' is not a PDF.</p><p>If you just uploaded it, please wait a moment for the conversion to finish and try again.</p></div>"
                                writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(msg_body, header_html, footer_html))))
                        except Exception as e:
                            frappe.log_error(f"Table row failure for {row.file}: {str(e)}", "Document Compilation")
            continue

        if section.get('file'):
            file_url = section['file']
            if file_url:
                try:
                    file_name = file_docs_map.get(file_url)
                    if not file_name:
                        continue
                    file_doc = frappe.get_doc("File", file_name)
                    sep_body = f"<div style='padding-top: 400px; text-align: center;'><h1>{frappe.utils.escape_html(section['title'])}</h1></div>"
                    writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(sep_body, header_html, footer_html))))
                    if file_doc.file_name.lower().endswith('.pdf'):
                        writer.append_pages_from_reader(PdfReader(BytesIO(file_doc.get_content())))
                    else:
                        msg_body = f"<div style='padding: 50px; text-align: center;'><p style='color:red;'><b>Unsupported File</b></p><p>File '{frappe.utils.escape_html(file_doc.file_name)}' is not a PDF.</p><p>Please convert it to PDF manually and re-upload.</p></div>"
                        writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(msg_body, header_html, footer_html))))
                except Exception as e:
                    frappe.log_error(f"File section failure for {file_url}: {str(e)}", "Document Compilation")


    output_stream = BytesIO()
    writer.write(output_stream)
    pdf_content = output_stream.getvalue()
    
    rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    timestamp = int(time.time())
    filename = frappe.utils.escape_html(f"{tender.name}_Compiled_Bid_{timestamp}_{rand_str}.pdf")
    
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": filename,
        "attached_to_doctype": "Tender Opportunity",
        "attached_to_name": tender.name,
        "content": pdf_content,
        "is_private": 1
    })
    file_doc.insert()
    
    tender.reload()
    tender.append("generated_documents", {
        "template": "Compiled Bid",
        "file": file_doc.file_url,
        "generated_by": frappe.session.user,
        "date": frappe.utils.now_datetime()
    })
    tender.save()
    
    return f"{file_doc.file_url}?v={timestamp}"

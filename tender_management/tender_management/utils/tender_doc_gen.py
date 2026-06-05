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
    
    # Letter Head HTML provided by user
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
    <!-- Reliable colored line replacement for gradient -->
    <div style="width: 100%; height: 2px; clear: both; margin-bottom: 15px;">
        <div style="float: left; width: 55%; height: 2px; background-color: #333132;"></div>
        <div style="float: left; width: 45%; height: 2px; background-color: #d92027;"></div>
    </div>
    """
    
    # Try to get real footer from DB if exists
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

    writer = PdfWriter()
    
    # 1. Add Cover Page
    cover_body = f"""
        <div style="text-align: center; padding-top: 100px;">
            <h1 style="color: #2c3e50; font-size: 32px; margin-bottom: 20px;">Compiled Technical Bid Package</h1>
            <h2 style="color: #7f8c8d; font-size: 24px; margin-bottom: 50px;">{tender.title}</h2>
            
            <div style="margin-top: 50px; font-size: 18px; line-height: 1.6; text-align: left; display: inline-block;">
                <p><strong>Tender Number:</strong> {tender.tender_number or 'N/A'}</p>
                <p><strong>Client:</strong> {tender.client or 'N/A'}</p>
                <p><strong>Sector:</strong> {tender.sector or 'N/A'}</p>
                <p><strong>Generated Date:</strong> {frappe.utils.format_datetime(frappe.utils.now_datetime())}</p>
            </div>
        </div>
    """
    cover_pdf_content = get_pdf_with_letterhead(cover_body)
    writer.append_pages_from_reader(PdfReader(BytesIO(cover_pdf_content)))
    
    # 1.5 Add Technical Proposal Cover Letter
    try:
        cover_letter_doc = frappe.get_doc("Document Template", "Technical Proposal Cover Letter")
        if cover_letter_doc and cover_letter_doc.content:
            # Prepare context for Jinja rendering
            context = tender.as_dict()
            company_settings = frappe.get_doc("Bid Document Management")
            context.update(company_settings.as_dict())
            
            # Additional typical template variables
            context.update({
                "company_name": "BESPO ELECTRO MECHANICAL SERVICES PLC",
                "organization": tender.client or "",
                "tender_title": tender.title or "",
                "submission_deadline": frappe.utils.formatdate(tender.submission_deadline) if tender.get("submission_deadline") else "",
                "tender_number": tender.tender_number or ""
            })
            
            # Render the template using Frappe's Jinja
            rendered_html = frappe.render_template(cover_letter_doc.content, context)
            
            writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(rendered_html))))
    except Exception as e:
        frappe.log_error(f"Failed to include Technical Proposal Cover Letter: {str(e)}", "Document Compilation")

    # 2. Add sections
    sections = [
        {"title": "1. Legal & Administrative", "table": "legal_and_administrative_documents"},
        {"title": "2. Our Company Profile", "table": "company_profile_documents"},
        {"title": "3. Our Employee List and CV", "table": "employee_list_cv_documents"},
        {"title": "4. Bid Submission Sheets", "file": tender.bid_submission_sheets},
        {"title": "5. Technical Methodology", "file": tender.technical_methodology},
        {"title": "6. Manufacturer Authorization Form (MAF)", "file": tender.manufacturer_authorization_form},
        {"title": "7. Supplier Company Profile", "file": tender.supplier_company_profile},
        {"title": "8. Supplier ISO and Other Certification", "file": tender.supplier_iso_certification},
        {"title": "9. The Bid Document", "file": tender.the_bid_document},
        {"title": "10. Financial Document", "file": tender.extracted_financial_document}
    ]
    
    for section in sections:
        # Handle Table-based sections
        if "table" in section:
            table_name = section["table"]
            rows = bid_mgmt.get(table_name) or []
            
            if rows:
                # Main separator
                main_sep_body = f"<div style='padding-top: 200px; text-align: center;'><h1>{section['title']}</h1></div>"
                writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(main_sep_body))))
                
                for row in rows:
                    if row.file:
                        try:
                            file_name_in_db = frappe.db.get_value("File", {"file_url": row.file}, "name")
                            if file_name_in_db:
                                file_doc = frappe.get_doc("File", file_name_in_db)
                                file_content = file_doc.get_content()
                                
                                if row.file.lower().endswith(".pdf"):
                                    writer.append_pages_from_reader(PdfReader(BytesIO(file_content)))
                                else:
                                    msg_body = f"<div style='padding: 50px; text-align: center;'><p>Non-PDF file: {file_doc.file_name}</p></div>"
                                    writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(msg_body))))
                        except Exception as e:
                            frappe.log_error(f"Failed to include row {row.document_title}: {str(e)}", "Document Compilation")
            continue

        # Handle File-based sections
        if section.get('file'):
            try:
                file_name_in_db = frappe.db.get_value("File", {"file_url": section['file']}, "name")
                if file_name_in_db:
                    file_doc = frappe.get_doc("File", file_name_in_db)
                    file_content = file_doc.get_content()
                    
                    # Section title/separator with letterhead
                    sep_body = f"<div style='padding-top: 200px; text-align: center;'><h1>{section['title']}</h1></div>"
                    writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(sep_body))))
                    
                    if section['file'].lower().endswith(".pdf"):
                        writer.append_pages_from_reader(PdfReader(BytesIO(file_content)))
                    else:
                        msg_body = f"<div style='padding: 50px; text-align: center;'><p>Non-PDF file: {file_doc.file_name}</p></div>"
                        writer.append_pages_from_reader(PdfReader(BytesIO(get_pdf_with_letterhead(msg_body))))
            except Exception as e:
                frappe.log_error(f"Failed to include section {section['title']}: {str(e)}", "Document Compilation")

            
    # 3. Finalize and Save
    output_stream = BytesIO()
    writer.write(output_stream)
    pdf_content = output_stream.getvalue()
    
    # Delete previously generated Compiled Bids
    if hasattr(tender, "generated_documents"):
        rows_to_remove = []
        for row in tender.generated_documents:
            if row.template == "Compiled Bid":
                rows_to_remove.append(row)
                # Attempt to delete the actual file
                if row.file:
                    try:
                        file_name = frappe.db.get_value("File", {"file_url": row.file}, "name")
                        if file_name:
                            frappe.delete_doc("File", file_name, ignore_permissions=True)
                    except Exception as e:
                        frappe.log_error(f"Failed to delete old compiled bid file: {str(e)}", "Document Cleanup")
        
        for row in rows_to_remove:
            tender.remove(row)

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


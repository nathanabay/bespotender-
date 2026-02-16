# Copyright (c) 2026, BES and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.pdf import get_pdf
import re

class DocumentTemplate(Document):
	def generate_document(self, tender_doc):
		"""
		Generate document from template by replacing placeholders with actual tender data
		Args:
			tender_doc: Tender Opportunity document
		Returns:
			str: Generated content with placeholders replaced
		"""
		content = self.content
		
		# Define placeholder mapping
		placeholders = {
			"tender_title": tender_doc.title or "",
			"organization": tender_doc.organization or "",
			"tender_number": tender_doc.tender_number or "",
			"submission_deadline": str(tender_doc.submission_deadline) if tender_doc.submission_deadline else "",
			"final_bid_price": str(tender_doc.final_bid_price) if tender_doc.final_bid_price else "",
			"sector": tender_doc.sector or "",
			"tender_type": tender_doc.tender_type or "",
			"company_name": frappe.defaults.get_defaults().get("company") or "BES"
		}
		
		# Replace placeholders
		for key, value in placeholders.items():
			pattern = r'\{\{' + key + r'\}\}'
			content = re.sub(pattern, value, content, flags=re.IGNORECASE)
		
		return content

@frappe.whitelist()
def download_pdf(html, tender_name, template_name, filename="document.pdf"):
	"""
	Generate and download PDF from HTML content and link it to the tender
	"""
	import frappe.utils
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
	file_doc.insert(ignore_permissions=True)
	
	# Add to Tender Opportunity child table
	try:
		tender = frappe.get_doc("Tender Opportunity", tender_name)
		tender.append("generated_documents", {
			"template": template_name,
			"file": file_doc.file_url,
			"generated_by": frappe.session.user,
			"date": frappe.utils.now_datetime()
		})
		tender.save(ignore_permissions=True)
	except Exception as e:
		frappe.log_error(f"Failed to link generated document: {str(e)}", "Document Generation")

	frappe.response.filename = filename
	frappe.response.filecontent = pdf_content
	frappe.response.type = "download"

@frappe.whitelist()
def generate_from_template(template_name, tender_name):
	"""
	Whitelisted function to generate document content from template
	Called from Tender Opportunity UI
	"""
	template = frappe.get_doc("Document Template", template_name)
	tender = frappe.get_doc("Tender Opportunity", tender_name)
	return template.generate_document(tender)

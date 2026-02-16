# Copyright (c) 2026, BES and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
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

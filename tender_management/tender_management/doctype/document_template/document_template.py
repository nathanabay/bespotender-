# Copyright (c) 2026, BES and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DocumentTemplate(Document):
    def autoname(self):
        self.name = self.template_name

    def validate(self):
        import re
        if self.content:
            placeholders = re.findall(r'\{(\w+)\}', self.content)
            self.placeholders = ", ".join(sorted(set(placeholders))) if placeholders else ""

    def generate_document(self, tender_doc):
        from tender_management.tender_management.utils.tender_doc_gen import generate_proposal_document
        return generate_proposal_document(self.name, tender_doc.name)

@frappe.whitelist()
def generate_from_template(template_name, tender_name):
    """
    Legacy catch-all for cached JS.
    """
    from tender_management.tender_management.utils.tender_doc_gen import generate_proposal_document
    return generate_proposal_document(template_name, tender_name)

@frappe.whitelist()
def generate_proposal_document(template_name, tender_name):
    """
    New whitelisted function.
    """
    from tender_management.tender_management.utils.tender_doc_gen import generate_proposal_document
    return generate_proposal_document(template_name, tender_name)

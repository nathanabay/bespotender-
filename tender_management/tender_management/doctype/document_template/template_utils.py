# Copyright (c) 2026, BES and contributors
# For license information, please see license.txt

import frappe

@frappe.whitelist()
def generate_from_template(template_name, tender_name):
    """
    Generate document content from template
    Args:
        template_name: Name of Document Template
        tender_name: Name of Tender Opportunity
    Returns:
        str: Generated HTML content
    """
    template = frappe.get_doc("Document Template", template_name)
    tender = frappe.get_doc("Tender Opportunity", tender_name)
    
    return template.generate_document(tender)

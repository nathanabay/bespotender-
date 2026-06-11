# Copyright (c) 2026, BES and contributors
# For license information, please see license.txt

import frappe
import unittest
from frappe.utils import random_string

from tender_management.utils.tender_doc_gen import generate_proposal_document

class TestDocumentGeneration(unittest.TestCase):
    def setUp(self):
        self.tender = self.create_test_tender()
        self.template = self.create_test_template()

    def tearDown(self):
        frappe.db.rollback()

    def create_test_tender(self):
        tender = frappe.get_doc({
            "doctype": "Tender Opportunity",
            "title": f"Test Tender {random_string(5)}",
            "client": "ACME Corporation",
            "tender_number": f"TND-{random_string(3)}",
            "final_bid_price": 50000,
            "submission_deadline": "2026-12-01 12:00:00",
            "sector": "Construction",
            "tender_type": "Request for Proposal (RFP)"
        })
        tender.insert()
        return tender

    def create_test_template(self):
        template = frappe.get_doc({
            "doctype": "Document Template",
            "template_name": f"Test Template {random_string(5)}",
            "doc_type": "Letter",
            "category": "Technical Proposal",
            "content": """
                <h1>Proposal for {{ tender_title }}</h1>
                <p>Client: {{ client }}</p>
                <p>Ref: {{ tender_number }}</p>
                <p>Our final offer is {{ final_bid_price }}.</p>
            """
        })
        template.insert()
        return template

    def test_placeholder_replacement(self):
        generated_content = generate_proposal_document(self.template.name, self.tender.name)
        self.assertNotIn("{{ tender_title }}", generated_content)
        self.assertNotIn("{{ client }}", generated_content)
        self.assertIn(self.tender.title, generated_content)
        self.assertIn(self.tender.client, generated_content)
        self.assertIn(self.tender.tender_number, generated_content)
        self.assertIn("50,000", generated_content)
        
        print("\nSUCCESS: Document Generation Test Passed!")
        print(f"Template: {self.template.name}")
        print(f"Tender: {self.tender.name}")
        print("\n--- Generated Content ---")
        print(generated_content)
        print("\n-------------------------")


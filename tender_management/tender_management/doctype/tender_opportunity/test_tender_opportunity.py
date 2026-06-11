import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import random_string

class TestTenderOpportunity(FrappeTestCase):
	def setUp(self):
		self.tender = frappe.get_doc({
			"doctype": "Tender Opportunity",
			"title": f"Test Opportunity {random_string(5)}",
			"client": "Test Client",
			"sector": "Construction",
			"tender_type": "Request for Proposal (RFP)",
			"final_bid_price": 100000,
			"bid_probability_score": 60,
			"submission_deadline": "2026-12-31 23:59:59"
		})
		self.tender.insert()

	def tearDown(self):
		frappe.db.rollback()

	def test_financial_calculations(self):
		self.tender.calculate_financials()
		# weighted_revenue = 60% of 100000 = 60000
		self.assertEqual(self.tender.weighted_revenue, 60000)

	def test_standard_tasks_creation(self):
		self.tender.create_standard_tasks()
		tasks = frappe.get_all("Tender Task", filters={"tender": self.tender.name})
		self.assertGreater(len(tasks), 0)


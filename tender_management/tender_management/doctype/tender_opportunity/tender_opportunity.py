import frappe
from frappe import _
from frappe.model.document import Document

class TenderOpportunity(Document):
	def validate(self):
		self.validate_tender_lifecycle()
		self.calculate_financials()
		self.auto_create_bid_security_request()
		self.validate_state_requirements()

	def calculate_financials(self):
		"""Automate financial calculations for forecasting and analytics"""
		if self.final_bid_price:
			self.revenue_potential = self.final_bid_price
		elif self.estimated_cost and not self.revenue_potential:
			self.revenue_potential = self.estimated_cost

		if self.revenue_potential and self.bid_probability_score:
			self.weighted_revenue = (self.bid_probability_score / 100.0) * self.revenue_potential
		else:
			self.weighted_revenue = 0

		if self.winning_bid_price and self.final_bid_price:
			self.price_difference = self.winning_bid_price - self.final_bid_price
		else:
			self.price_difference = 0

		if self.bond_percentage:
			base_for_bond = self.final_bid_price or self.estimated_cost
			if base_for_bond:
				self.bond_amount = (self.bond_percentage / 100.0) * base_for_bond

	def validate_tender_lifecycle(self):
		"""Relaxed date validation to support internal decisions"""
		import frappe.utils
		
		if self.publication_date and self.submission_deadline:
			if frappe.utils.get_datetime(self.publication_date) > frappe.utils.get_datetime(self.submission_deadline):
				frappe.throw(_("Publication Date ({0}) cannot be after Submission Deadline ({1})")
					.format(self.publication_date, frappe.utils.format_datetime(self.submission_deadline)))

	def after_insert(self):
		self.create_standard_tasks()

	def create_standard_tasks(self):
		"""Create standard tasks for new tender opportunity"""
		self.check_permission("write")
		import frappe.utils
		tasks = [
			{"title": "Review Tender Requirements", "priority": "High", "days": 2, "description": "Review the tender document."},
			{"title": "Bid/No-Bid Decision", "priority": "High", "days": 3, "description": "Make a formal bid/no-bid decision."},
			{"title": "Prepare Technical Proposal", "priority": "Medium", "days": 7, "description": "Draft the technical response."},
			{"title": "Prepare Financial Proposal", "priority": "Medium", "days": 7, "description": "Calculate costs."},
			{"title": "Obtain Bid Security", "priority": "High", "days": 5, "description": "Request the bid bond."},
			{"title": "Final Quality Review", "priority": "Medium", "days": 10, "description": "Final quality review."},
			{"title": "Submission Confirmation", "priority": "High", "days": 12, "description": "Submit the proposal."}
		]
		# Pre-fetch all existing task titles in one query to avoid N+1 db.exists calls
		existing_titles = set(
			frappe.get_all(
				"Tender Task",
				filters={"tender": self.name},
				pluck="title"
			)
		)
		for task_data in tasks:
			if task_data["title"] not in existing_titles:
				task = frappe.new_doc("Tender Task")
				task.tender = self.name
				task.title = task_data["title"]
				task.description = task_data["description"]
				task.priority = task_data["priority"]
				task.status = "Open"
				task.due_date = frappe.utils.add_days(frappe.utils.nowdate(), task_data["days"])
				task.assigned_to = self.owner or frappe.session.user
				task.insert()

	def validate_state_requirements(self):
		state = self.workflow_state
		if state == "Tender Purchased":
			if not self.purchase_date or not self.purchase_receipt_no:
				frappe.throw(_("Purchase Date and Receipt Number are required to transition to 'Tender Purchased'"))
		
		if state == "Bid Bond Issued":
			if not self.bid_security_request:
				frappe.throw(_("Please link a 'Bid Security Request'"))
			status = frappe.db.get_value("Bid Security Request", self.bid_security_request, "status")
			if status != "Issued":
				frappe.throw(_("The linked Bid Security Request must be 'Issued'."))

	def auto_create_bid_security_request(self):
		if self.workflow_state != "Tender Purchased" or self.bid_security_request or not self.bond_amount:
			return
		
		bank_account = frappe.db.get_value("Account", {"account_type": "Bank", "is_group": 0, "disabled": 0}, "name")
		if not bank_account: return

		try:
			bsr = frappe.new_doc("Bid Security Request")
			bsr.tender = self.name
			bsr.type = self.bond_type or "CPO"
			bsr.amount = self.bond_amount
			bsr.validity_period_days = self.bond_validity_days or 90
			bsr.bank_account = bank_account
			bsr.status = "Draft"
			bsr.required_date = self.submission_deadline or frappe.utils.nowdate()
			bsr.insert(ignore_permissions=True)
			# Assign to self directly — db_set inside validate() gets overwritten by save()
			self.bid_security_request = bsr.name
		except Exception as e:
			frappe.log_error(f"BSR Auto-Creation Error: {str(e)}", "BSR Auto-Creation")

	@frappe.whitelist()
	def toggle_watch(self):
		self.check_permission("read")
		user = frappe.session.user
		existing = frappe.db.exists("Tender Follower", {"parent": self.name, "parenttype": self.doctype, "user": user})
		if existing:
			frappe.db.delete("Tender Follower", existing)
			self.db_set("modified", frappe.utils.now())
			return False
		else:
			follower = frappe.new_doc("Tender Follower")
			follower.parent = self.name
			follower.parenttype = self.doctype
			follower.parentfield = "followers"
			follower.user = user
			follower.insert(ignore_permissions=True)
			self.db_set("modified", frappe.utils.now())
			return True

@frappe.whitelist()
def generate_compiled_tender_document_final(tender_name):
    if not frappe.has_permission("Tender Opportunity", "read", doc=tender_name):
        frappe.throw(frappe._("Not permitted to compile documents for this Tender Opportunity"), frappe.PermissionError)
    from tender_management.utils.tender_doc_gen import generate_compiled_tender_document_v5
    return generate_compiled_tender_document_v5(tender_name)

@frappe.whitelist()
def create_standard_tasks_for(tender_name):
    doc = frappe.get_doc("Tender Opportunity", tender_name)
    doc.check_permission("write")
    doc.create_standard_tasks()

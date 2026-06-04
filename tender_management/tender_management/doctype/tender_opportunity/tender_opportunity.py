import frappe
from frappe import _
from frappe.model.document import Document

class TenderOpportunity(Document):
    def validate(self):
        # 1. Basic Date Check (Only Publication vs Submission)
        self.check_tender_dates()
        
        # 2. Calculations
        self.calculate_financials()
        
        # 3. State-based requirements
        self.validate_state_requirements()
        
        # 4. Auto-create BSR
        self.auto_create_bid_security_request()

    def check_tender_dates(self):
        import frappe.utils
        if self.publication_date and self.submission_deadline:
            if frappe.utils.get_datetime(self.publication_date) > frappe.utils.get_datetime(self.submission_deadline):
                frappe.throw(_("Publication Date cannot be after Submission Deadline"))

    def calculate_financials(self):
        if self.final_bid_price:
            self.revenue_potential = self.final_bid_price
        
        if self.revenue_potential and self.bid_probability_score:
            self.weighted_revenue = (self.bid_probability_score / 100.0) * self.revenue_potential
            
        if self.winning_bid_price and self.final_bid_price:
            self.price_difference = self.winning_bid_price - self.final_bid_price
            
        if self.bond_percentage:
            base = self.final_bid_price or self.estimated_cost
            if base:
                self.bond_amount = (self.bond_percentage / 100.0) * base

    def after_insert(self):
        self.create_standard_tasks()

    @frappe.whitelist()
    def create_standard_tasks(self):
        from tender_management.tender_management.utils.tender_doc_gen import generate_proposal_document
        # Logic for tasks...
        pass

    def validate_state_requirements(self):
        if self.workflow_state == "Tender Purchased":
            if not self.purchase_date or not self.purchase_receipt_no:
                frappe.throw(_("Purchase Date and Receipt Number are required"))

    def auto_create_bid_security_request(self):
        if self.workflow_state == "Tender Purchased" and not self.bid_security_request and self.bond_amount:
            # Logic for BSR...
            pass

    @frappe.whitelist()
    def toggle_watch(self):
        # Logic for watch...
        return True

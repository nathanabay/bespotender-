import frappe
from frappe import _
from frappe.model.document import Document

class TenderOpportunity(Document):
    def validate(self):
        # Auto-create Bid Security Request when moving to Tender Purchased
        self.auto_create_bid_security_request()
        self.validate_state_requirements()

    def validate_state_requirements(self):
        state = self.workflow_state
        
        if state == "Tender Purchased":
            if not self.purchase_date or not self.purchase_receipt_no:
                frappe.throw(_("Purchase Date and Receipt Number are required to transition to 'Tender Purchased'"))
        
        if state == "Bid Bond Issued":
            if not self.bid_security_request:
                frappe.throw(_("Please link a 'Bid Security Request' before transitioning to 'Bid Bond Issued'"))
            
            # Check if the request is actually issued
            status = frappe.db.get_value("Bid Security Request", self.bid_security_request, "status")
            if status != "Issued":
                frappe.throw(_("The linked Bid Security Request must be 'Issued' before proceeding."))
        
        if state == "Ready for Submission":
            if not self.technical_proposal or not self.financial_proposal_doc:
                frappe.throw(_("Technical and Financial Proposals are required to transition to 'Ready for Submission'"))

    def auto_create_bid_security_request(self):
        """Auto-create Bid Security Request when tender reaches 'Tender Purchased' state"""
        # Only proceed if workflow state is Tender Purchased
        if self.workflow_state != "Tender Purchased":
            return
        
        # Skip if already linked to a Bid Security Request
        if self.bid_security_request:
            return
        
        # Skip if no bond amount specified
        if not self.bond_amount:
            return
        
        # Get default bank account - first available bank account
        bank_account = frappe.db.get_value("Account", {
            "account_type": "Bank",
            "is_group": 0,
            "disabled": 0
        }, "name")
        
        if not bank_account:
            frappe.msgprint(_("No bank account found. Please create a Bid Security Request manually."), alert=True)
            return
        
        # Create the Bid Security Request
        try:
            bsr = frappe.new_doc("Bid Security Request")
            bsr.tender_opportunity = self.name
            bsr.type = self.bond_type or "CPO"
            bsr.amount = self.bond_amount
            bsr.validity_period_days = self.bond_validity_days or 90
            bsr.bank_account = bank_account
            bsr.status = "Draft"
            bsr.required_date = self.submission_deadline or frappe.utils.nowdate()
            bsr.insert(ignore_permissions=True)
            
            # Link back to tender using db_set to avoid recursive validation
            self.db_set('bid_security_request', bsr.name, update_modified=False)
            
            frappe.msgprint(_("Bid Security Request {0} created automatically").format(bsr.name), alert=True, indicator="green")
            
        except Exception as e:
            error_msg = str(e)
            frappe.log_error(f"BSR Auto-Creation Error for {self.name}: {error_msg}", "BSR Auto-Creation")
            frappe.msgprint(_("Error: {0}. Please create Bid Security Request manually.").format(error_msg), alert=True, indicator="red")

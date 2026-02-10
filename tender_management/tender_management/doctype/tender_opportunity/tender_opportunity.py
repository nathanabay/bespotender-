import frappe
from frappe import _
from frappe.model.document import Document

class TenderOpportunity(Document):
    def validate(self):
        self.validate_state_requirements()

    def validate_state_requirements(self):
        state = self.workflow_state
        
        if state == "Tender Purchased":
            if not self.purchase_date or not self.purchase_receipt_no:
                frappe.throw(_("Purchase Date and Receipt Number are required to transition to 'Tender Purchased'"))
        
        if state == "Bid Bond Issued":
            if not self.bond_number or not self.bank_name:
                frappe.throw(_("Bond Number and Bank Name are required to transition to 'Bid Bond Issued'"))
        
        if state == "Ready for Submission":
            if not self.technical_proposal or not self.financial_proposal_doc:
                frappe.throw(_("Technical and Financial Proposals are required to transition to 'Ready for Submission'"))

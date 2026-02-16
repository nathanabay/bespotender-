import frappe
from frappe import _
from frappe.model.document import Document

class TenderOpportunity(Document):
    def validate(self):
        # Auto-create Bid Security Request when moving to Tender Purchased
        self.auto_create_bid_security_request()
        self.validate_state_requirements()

    def after_insert(self):
        self.create_standard_tasks()

    @frappe.whitelist()
    def create_standard_tasks(self):
        """Create standard tasks for new tender opportunity"""
        import frappe.utils

        # Define standard tasks with relative due dates
        tasks = [
            {"title": "Review Tender Requirements", "priority": "High", "days": 2, "description": "Review the tender document and identify key requirements (eligibility, technical, financial)."},
            {"title": "Bid/No-Bid Decision", "priority": "High", "days": 3, "description": "Conduct risk analysis, cost-benefit analysis, and make a formal bid/no-bid decision."},
            {"title": "Prepare Technical Proposal", "priority": "Medium", "days": 7, "description": "Draft the technical response, methodology, and compliance matrix."},
            {"title": "Prepare Financial Proposal", "priority": "Medium", "days": 7, "description": "Calculate costs, prepare BOQ, and determine final pricing strategy."},
            {"title": "Obtain Bid Security", "priority": "High", "days": 5, "description": "Request and obtain the bid bond (CPO/Bank Guarantee) from the bank."},
            {"title": "Final Quality Review", "priority": "Medium", "days": 10, "description": "Conduct a final quality review of the proposal documents and compliance check."},
            {"title": "Submission Confirmation", "priority": "High", "days": 12, "description": "Submit the proposal and obtain submission confirmation/receipt."}
        ]

        created_count = 0
        skipped_count = 0
        for task_data in tasks:
            # Skip if task with same title already exists for this tender
            if frappe.db.exists("Tender Task", {"tender": self.name, "title": task_data["title"]}):
                skipped_count += 1
                continue

            try:
                task = frappe.new_doc("Tender Task")
                task.tender = self.name
                task.title = task_data["title"]
                task.description = task_data["description"]
                task.priority = task_data["priority"]
                task.status = "Open"
                task.due_date = frappe.utils.add_days(frappe.utils.nowdate(), task_data["days"])
                task.assigned_to = self.owner or frappe.session.user
                task.insert(ignore_permissions=True)
                created_count += 1
            except Exception as e:
                frappe.log_error(f"Failed to auto-create task {task_data['title']}: {str(e)}", "Tender Task Auto-Creation")

        if created_count > 0:
            msg = _("{0} Standard Tender Tasks Created").format(created_count)
            if skipped_count > 0:
                msg += _(" ({0} skipped as they already exist)").format(skipped_count)
            frappe.msgprint(msg, alert=True, indicator="green")
        elif skipped_count > 0 and frappe.request:
            frappe.msgprint(_("All {0} standard tasks already exist.").format(skipped_count), alert=True)

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
            bsr.tender = self.name
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

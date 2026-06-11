# Copyright (c) 2026, Administrator and contributors
# For license information, please see license.txt

import frappe
import frappe.utils
from frappe.model.document import Document

class BidSecurityRequest(Document):
	def validate(self):
		if self.status == "Issued" and not self.security_number:
			frappe.throw("Security Number is required when status is Issued")
			
	def before_submit(self):
		if self.status == "Issued" and not self.journal_entry:
			self.create_journal_entry()

	def create_journal_entry(self):
		if not self.amount or not self.bank_account:
			frappe.throw("Amount and Bank Account are required to create a Journal Entry")

		# Find a default account for Bid Bond Receivable
		# In a real scenario, this should be in Company settings. 
		# For now, we search for an account with the configured pattern or 'Bid Bond' in the name.
		bid_bond_search = frappe.conf.get('bid_bond_account', 'Bid Bond')
		bid_bond_account = frappe.db.get_value("Account", {"account_name": ["like", f"%{bid_bond_search}%"], "company": frappe.defaults.get_user_default("Company")}, "name")
		
		if not bid_bond_account:
			# Fallback or error
			frappe.throw(f"Could not find an Account matching '{bid_bond_search}'. Please create one in the Chart of Accounts.")

		je = frappe.new_doc("Journal Entry")
		je.posting_date = self.required_date or frappe.utils.nowdate()
		je.company = frappe.defaults.get_user_default("Company")
		je.voucher_type = "Bank Entry"
		je.cheque_no = self.security_number
		je.cheque_date = self.required_date
		
		# Debit: Bid Bond Receivable (Asset)
		je.append("accounts", {
			"account": bid_bond_account,
			"debit_in_account_currency": self.amount,
			"party_type": "Supplier", # If linked to Customer/Supplier, change this
			"party": self.tender, # Linking to Tender Opp if possible, or keeping empty
			"reference_type": "Bid Security Request",
			"reference_name": self.name
		})
		
		# Credit: Bank Account (Asset)
		je.append("accounts", {
			"account": self.bank_account,
			"credit_in_account_currency": self.amount,
			"reference_type": "Bid Security Request",
			"reference_name": self.name
		})
		
		je.save()
		je.submit()
		
		self.journal_entry = je.name
		frappe.msgprint(f"Journal Entry {je.name} created automatically.")

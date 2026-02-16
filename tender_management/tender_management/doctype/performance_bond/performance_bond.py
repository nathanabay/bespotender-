# Copyright (c) 2026, BES and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PerformanceBond(Document):
	def validate(self):
		if self.expiry_date and self.issue_date:
			if self.expiry_date < self.issue_date:
				frappe.throw("Expiry date cannot be before issue date")

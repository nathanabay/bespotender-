# Copyright (c) 2026, BES and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CostItem(Document):
	def validate(self):
		self.calculate_total()
	
	def calculate_total(self):
		"""Calculate total cost from quantity and unit cost"""
		self.total_cost = (self.quantity or 0) * (self.unit_cost or 0)

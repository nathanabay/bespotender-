# Copyright (c) 2026, BES and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CostEstimation(Document):
	def validate(self):
		self.calculate_totals()
	
	def calculate_totals(self):
		"""Calculate total direct cost, overhead, profit, and final price"""
		# Calculate total direct cost from items
		total_direct_cost = 0
		for item in self.items:
			total_direct_cost += item.total_cost or 0
		
		self.total_direct_cost = total_direct_cost
		
		# Calculate overhead
		overhead_pct = (self.overhead_percentage or 0) / 100
		self.overhead_amount = self.total_direct_cost * overhead_pct
		
		# Calculate profit
		subtotal = self.total_direct_cost + self.overhead_amount
		profit_pct = (self.profit_margin_percentage or 0) / 100
		self.profit_amount = subtotal * profit_pct
		
		# Calculate total price
		self.total_price = subtotal + self.profit_amount

# Copyright (c) 2026, BES and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today

class BidDecisionMatrix(Document):
	def validate(self):
		self.calculate_score()
		self.suggest_decision()
	
	def calculate_score(self):
		"""Calculate total score from all criteria"""
		self.total_score = (
			(self.win_probability_score or 0) +
			(self.profitability_score or 0) +
			(self.strategic_fit_score or 0) +
			(self.resource_availability_score or 0) +
			(self.technical_capability_score or 0) +
			(self.client_relationship_score or 0) +
			(self.competition_intensity_score or 0)
		)
	
	def suggest_decision(self):
		"""Auto-suggest decision based on total score"""
		if self.total_score >= 50:
			self.suggested_decision = "Bid"
		else:
			self.suggested_decision = "No-Bid"
		
		# Set decision date if not set
		if not self.decision_date:
			self.decision_date = today()

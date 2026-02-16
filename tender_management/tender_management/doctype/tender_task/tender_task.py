# Copyright (c) 2026, BES and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today

class TenderTask(Document):
	def validate(self):
		# Auto-set completion date when status is changed to Completed
		if self.status == "Completed" and not self.completion_date:
			self.completion_date = today()
	
	def on_update(self):
		# Notify assignee when task is assigned or updated
		if self.assigned_to and self.has_value_changed('assigned_to'):
			self.notify_assignee()
	
	def notify_assignee(self):
		"""Send notification to the assigned user"""
		if self.assigned_to:
			subject = f"Task Assigned: {self.title}"
			message = f"""
				You have been assigned a new task for tender: {self.tender}
				
				Task: {self.title}
				Due Date: {self.due_date}
				Priority: {self.priority}
				
				Please review and update the task status accordingly.
			"""
			frappe.publish_realtime(
				event='task_assigned',
				message={'task': self.name, 'title': self.title},
				user=self.assigned_to
			)

"""
tender_management/tender_management/setup/notifications.py

Creates system Notifications and User Custom Fields for tender alerts.
"""
import frappe


def setup_notifications():
	print("🔔 Setting up Notifications...")

	# 1. Tender Deadline Alert
	if not frappe.db.exists("Notification", "Tender Deadline Alert"):
		frappe.get_doc({
			"doctype": "Notification",
			"name": "Tender Deadline Alert",
			"document_type": "Tender Opportunity",
			"event": "Days Before",
			"days_before_after": 2,
			"date_changed": "submission_deadline",
			"channel": "System Notification",
			"enabled": 1,
			"subject": "Tender Submission Deadline Tomorrow: {{ doc.name }}",
			"message": "The tender <b>{{ doc.title }}</b> is closing tomorrow ({{ doc.submission_deadline }}). Please ensure preparation is complete."
		}).insert(ignore_permissions=True)
		print("  ✔ Created Notification: Tender Deadline Alert")

	# 2. CPO Expiry Alert
	if not frappe.db.exists("Notification", "CPO Expiry Alert"):
		frappe.get_doc({
			"doctype": "Notification",
			"name": "CPO Expiry Alert",
			"document_type": "Bid Security",
			"event": "Days Before",
			"days_before_after": 7,
			"date_changed": "expiry_date",
			"channel": "System Notification",
			"enabled": 1,
			"subject": "CPO Expiring Soon: {{ doc.name }}",
			"message": "The Bid Security (CPO) for Tender <b>{{ doc.tender }}</b> expires in 7 days."
		}).insert(ignore_permissions=True)
		print("  ✔ Created Notification: CPO Expiry Alert")


def setup_user_custom_fields():
	"""
	Add notification preference fields to the User DocType
	"""
	print("👤 Setting up User Custom Fields...")
	
	custom_fields = [
		{
			"fieldname": "receive_tender_deadline_alerts",
			"label": "Receive Tender Deadline Alerts",
			"fieldtype": "Check",
			"insert_after": "email_notifications",
			"default": "1"
		},
		{
			"fieldname": "receive_workflow_state_alerts",
			"label": "Receive Workflow State Alerts",
			"fieldtype": "Check",
			"insert_after": "receive_tender_deadline_alerts",
			"default": "1"
		},
		{
			"fieldname": "receive_cpo_expiry_alerts",
			"label": "Receive CPO Expiry Alerts",
			"fieldtype": "Check",
			"insert_after": "receive_workflow_state_alerts",
			"default": "1"
		}
	]
	
	for field in custom_fields:
		if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": field["fieldname"]}):
			frappe.get_doc({
				"doctype": "Custom Field",
				"dt": "User",
				**field
			}).insert(ignore_permissions=True)
			print(f"  ✔ Created Custom Field: {field['fieldname']}")
		else:
			# Update label or other properties if they changed
			doc = frappe.get_doc("Custom Field", {"dt": "User", "fieldname": field["fieldname"]})
			doc.update(field)
			doc.save(ignore_permissions=True)
			print(f"  ✔ Updated Custom Field: {field['fieldname']}")

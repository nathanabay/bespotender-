"""
tender_management/tender_management/setup/workflow.py

Updates the Two-Stage Tender Approval workflow states and transitions.
"""
import frappe


def setup_enhanced_workflow():
	wf_name = "Two-Stage Tender Approval"
	if not frappe.db.exists("Workflow", wf_name):
		print(f"  ⚠ Workflow not found, skipping: {wf_name}")
		return

	doc = frappe.get_doc("Workflow", wf_name)

	# Ensure Workflow Actions exist
	for action in [
		"Confirm Purchase", "Issue Bond", "Start Technical",
		"Start Financial", "Finalize", "Submit Bid",
		"Award Tender", "Regret",
	]:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(ignore_permissions=True)
			print(f"  ✔ Created Workflow Action: {action}")

	doc.set("states", [])
	for s in [
		{"state": "Draft", "allow_edit": "Tender User", "doc_status": "0"},
		{"state": "Pending Review", "allow_edit": "Tender Manager", "doc_status": "0"},
		{"state": "Pending Final Approval", "allow_edit": "Tender Director", "doc_status": "0"},
		{"state": "Approved to Bid", "allow_edit": "Tender Manager", "doc_status": "0"},
		{"state": "Tender Purchased", "allow_edit": "Tender Manager", "doc_status": "0"},
		{"state": "Bid Bond Issued", "allow_edit": "Tender Manager", "doc_status": "0"},
		{"state": "Technical Preparation", "allow_edit": "Tender Manager", "doc_status": "0"},
		{"state": "Financial Preparation", "allow_edit": "Tender Manager", "doc_status": "0"},
		{"state": "Ready for Submission", "allow_edit": "Tender Manager", "doc_status": "0"},
		{"state": "Submitted", "allow_edit": "Tender Manager", "doc_status": "1"},
		{"state": "Won", "allow_edit": "Tender Manager", "doc_status": "1"},
		{"state": "Lost", "allow_edit": "Tender Manager", "doc_status": "2"},
		{"state": "Rejected", "allow_edit": "Tender User", "doc_status": "0"},
	]:
		doc.append("states", s)

	doc.set("transitions", [])
	for t in [
		{"state": "Draft", "action": "Submit for Review", "next_state": "Pending Review", "allowed": "Tender User"},
		{"state": "Pending Review", "action": "Approve (Level 1)", "next_state": "Pending Final Approval", "allowed": "Tender Manager"},
		{"state": "Pending Review", "action": "Reject", "next_state": "Rejected", "allowed": "Tender Manager"},
		{"state": "Pending Final Approval", "action": "Approve (Final)", "next_state": "Approved to Bid", "allowed": "Tender Director"},
		{"state": "Pending Final Approval", "action": "Reject", "next_state": "Rejected", "allowed": "Tender Director"},
		{"state": "Approved to Bid", "action": "Confirm Purchase", "next_state": "Tender Purchased", "allowed": "Tender Manager"},
		{"state": "Tender Purchased", "action": "Issue Bond", "next_state": "Bid Bond Issued", "allowed": "Tender Manager"},
		{"state": "Bid Bond Issued", "action": "Start Technical", "next_state": "Technical Preparation", "allowed": "Tender Manager"},
		{"state": "Technical Preparation", "action": "Start Financial", "next_state": "Financial Preparation", "allowed": "Tender Manager"},
		{"state": "Financial Preparation", "action": "Finalize", "next_state": "Ready for Submission", "allowed": "Tender Manager"},
		{"state": "Ready for Submission", "action": "Submit Bid", "next_state": "Submitted", "allowed": "Tender Manager"},
		{"state": "Submitted", "action": "Award Tender", "next_state": "Won", "allowed": "Tender Director"},
		{"state": "Submitted", "action": "Regret", "next_state": "Lost", "allowed": "Tender Director"},
		{"state": "Rejected", "action": "Restart", "next_state": "Draft", "allowed": "Tender User"},
	]:
		doc.append("transitions", t)
		# Duplicate with System Manager to prevent role deadlocks
		sm_t = t.copy()
		sm_t["allowed"] = "System Manager"
		doc.append("transitions", sm_t)

	doc.save(ignore_permissions=True)
	print(f"  ✔ Workflow updated: {wf_name}")

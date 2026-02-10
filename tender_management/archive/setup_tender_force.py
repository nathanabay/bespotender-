import frappe

def run():
    print("--- ⚡ RUNNING FORCED WORKFLOW INSTALLATION ---")

    # 1. ENSURE ACTIONS EXIST (SQL METHOD)
    # We repeat this to be absolutely sure they are there
    actions = ["Approve for Purchase", "Assign Buyer", "Upload Documents", "Start Proposal", "Submit for Review", "Approve Bid", "Reject Bid"]
    
    for a in actions:
        if not frappe.db.exists("Workflow Action", a):
            frappe.db.sql("""
                INSERT INTO `tabWorkflow Action` (name, creation, modified, modified_by, owner, docstatus)
                VALUES (%s, NOW(), NOW(), 'Administrator', 'Administrator', 0)
            """, (a,))
            print(f"✔ Action confirmed: {a}")

    frappe.db.commit()

    # 2. DEFINE WORKFLOW
    wf_name = "Tender Lifecycle"
    if frappe.db.exists("Workflow", wf_name):
        frappe.delete_doc("Workflow", wf_name)

    wf = frappe.get_doc({
        "doctype": "Workflow",
        "workflow_name": wf_name,
        "document_type": "Tender Opportunity",
        "workflow_state_field": "workflow_state",
        "is_active": 1,
        "states": [
            {"state": "Identified", "doc_status": 0, "allow_edit": "System Manager", "update_field": "workflow_state"},
            {"state": "To Buy", "doc_status": 0, "allow_edit": "System Manager", "update_field": "workflow_state"},
            {"state": "Buying", "doc_status": 0, "allow_edit": "System Manager", "update_field": "workflow_state"},
            {"state": "Scanning", "doc_status": 0, "allow_edit": "System Manager", "update_field": "workflow_state"},
            {"state": "Proposal", "doc_status": 0, "allow_edit": "System Manager", "update_field": "workflow_state"},
            {"state": "Review", "doc_status": 0, "allow_edit": "System Manager", "update_field": "workflow_state"},
            {"state": "Approved", "doc_status": 1, "allow_edit": "System Manager", "update_field": "workflow_state"},
            {"state": "Rejected", "doc_status": 2, "allow_edit": "System Manager", "update_field": "workflow_state"}
        ],
        "transitions": [
            {"state": "Identified", "action": "Approve for Purchase", "next_state": "To Buy", "allowed": "System Manager"},
            {"state": "To Buy", "action": "Assign Buyer", "next_state": "Buying", "allowed": "System Manager"},
            {"state": "Buying", "action": "Upload Documents", "next_state": "Scanning", "allowed": "System Manager"},
            {"state": "Scanning", "action": "Start Proposal", "next_state": "Proposal", "allowed": "System Manager"},
            {"state": "Proposal", "action": "Submit for Review", "next_state": "Review", "allowed": "System Manager"},
            {"state": "Review", "action": "Approve Bid", "next_state": "Approved", "allowed": "System Manager"},
            {"state": "Review", "action": "Reject Bid", "next_state": "Rejected", "allowed": "System Manager"}
        ]
    })
    
    # 3. FORCE INSERT (IGNORE VALIDATION)
    # This assumes we know what we are doing (and we do).
    wf.flags.ignore_links = True 
    wf.insert(ignore_permissions=True)
    
    frappe.db.commit()
    print("--- ✅ SUCCESS: TENDER WORKFLOW FORCED SUCCESSFULLY ---")

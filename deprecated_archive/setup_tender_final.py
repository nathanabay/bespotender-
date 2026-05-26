import frappe

def run():
    print("--- 🔧 FINALIZING TENDER WORKFLOW ---")

    # 1. DEFINE STATES & ACTIONS
    states = ["Identified", "To Buy", "Buying", "Scanning", "Proposal", "Review", "Approved", "Rejected"]
    actions = ["Approve for Purchase", "Assign Buyer", "Upload Documents", "Start Proposal", "Submit for Review", "Approve Bid", "Reject Bid"]

    # 2. CREATE MISSING STATES
    for s in states:
        if not frappe.db.exists("Workflow State", s):
            style = "Inverse"
            if s == "Approved": style = "Success"
            elif s == "Rejected": style = "Danger"
            elif s == "Review": style = "Warning"
            elif s == "Buying": style = "Info"

            frappe.get_doc({
                "doctype": "Workflow State",
                "workflow_state_name": s,
                "style": style
            }).insert(ignore_permissions=True)
            print(f"✔ Created State: {s}")

    # 3. CREATE MISSING ACTIONS
    for a in actions:
        if not frappe.db.exists("Workflow Action", a):
            frappe.get_doc({
                "doctype": "Workflow Action",
                "workflow_action_name": a
            }).insert(ignore_permissions=True)
            print(f"✔ Created Action: {a}")

    # --- CRITICAL FIX: COMMIT NOW SO THEY EXIST FOR LINKING ---
    frappe.db.commit()

    # 4. NOW CREATE THE WORKFLOW
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
    wf.insert(ignore_permissions=True)
    
    frappe.db.commit()
    print("--- ✅ SUCCESS: WORKFLOW ACTIVE ---")

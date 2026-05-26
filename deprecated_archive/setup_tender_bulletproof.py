import frappe

def run():
    print("--- 🛡️ RUNNING BULLETPROOF WORKFLOW SETUP ---")

    # 1. DEFINE DATA
    states = [
        {"name": "Identified", "style": "Inverse"},
        {"name": "To Buy", "style": "Inverse"},
        {"name": "Buying", "style": "Info"},
        {"name": "Scanning", "style": "Inverse"},
        {"name": "Proposal", "style": "Inverse"},
        {"name": "Review", "style": "Warning"},
        {"name": "Approved", "style": "Success"},
        {"name": "Rejected", "style": "Danger"}
    ]
    
    actions = [
        "Approve for Purchase", "Assign Buyer", "Upload Documents", 
        "Start Proposal", "Submit for Review", "Approve Bid", "Reject Bid"
    ]

    # 2. CREATE STATES (Force Name)
    for s in states:
        if not frappe.db.exists("Workflow State", s["name"]):
            d = frappe.get_doc({
                "doctype": "Workflow State",
                "workflow_state_name": s["name"],
                "style": s["style"]
            })
            d.name = s["name"] # Explicit assignment
            d.insert(ignore_permissions=True)
    print("✔ States Verified")

    # 3. CREATE ACTIONS (Force Name using SQL if Doc API fails)
    # This acts as a fallback to ensure the Link field finds exactly what it expects
    for a in actions:
        if not frappe.db.exists("Workflow Action", a):
            try:
                d = frappe.get_doc({
                    "doctype": "Workflow Action",
                    "workflow_action_name": a
                })
                d.name = a # Attempt standard force
                d.insert(ignore_permissions=True)
            except Exception:
                # If standard insert fails/renames, force via SQL
                frappe.db.sql("""
                    INSERT INTO `tabWorkflow Action` (name, workflow_action_name, creation, modified, modified_by, owner, docstatus)
                    VALUES (%s, %s, NOW(), NOW(), 'Administrator', 'Administrator', 0)
                """, (a, a))
                frappe.db.commit()
    print("✔ Actions Verified")

    frappe.db.commit() # Ensure they exist before linking

    # 4. CREATE WORKFLOW
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
    
    print("--- ✅ WORKFLOW INSTALLED SUCCESSFULLY ---")

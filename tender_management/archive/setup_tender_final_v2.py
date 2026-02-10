import frappe

def run():
    print("--- 🚀 FINAL FIX: SQL FORCE SETUP (Using 'action' column) ---")

    # 1. FIX STATES
    states = [
        ("Identified", "Inverse"), ("To Buy", "Inverse"), ("Buying", "Info"),
        ("Scanning", "Inverse"), ("Proposal", "Inverse"), ("Review", "Warning"),
        ("Approved", "Success"), ("Rejected", "Danger")
    ]
    
    print("... Fixing States")
    for s_name, s_style in states:
        if not frappe.db.exists("Workflow State", s_name):
            frappe.db.sql("""
                INSERT INTO `tabWorkflow State` (name, workflow_state_name, style, creation, modified, modified_by, owner, docstatus)
                VALUES (%s, %s, %s, NOW(), NOW(), 'Administrator', 'Administrator', 0)
            """, (s_name, s_name, s_style))
            print(f"✔ State: {s_name}")

    # 2. FIX ACTIONS (The Fix is here: using 'action' column)
    actions = ["Approve for Purchase", "Assign Buyer", "Upload Documents", "Start Proposal", "Submit for Review", "Approve Bid", "Reject Bid"]
    
    print("... Fixing Actions")
    for a in actions:
        if not frappe.db.exists("Workflow Action", a):
            try:
                # Try inserting using 'action' column which is standard in your version
                frappe.db.sql("""
                    INSERT INTO `tabWorkflow Action` (name, action, creation, modified, modified_by, owner, docstatus)
                    VALUES (%s, %s, NOW(), NOW(), 'Administrator', 'Administrator', 0)
                """, (a, a))
                print(f"✔ Action: {a}")
            except Exception as e:
                print(f"⚠️ SQL Warning for {a}: {e}")

    frappe.db.commit()

    # 3. CREATE WORKFLOW
    print("... Linking Workflow")
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
    print("--- ✅ DONE ---")

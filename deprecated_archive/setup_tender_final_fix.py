import frappe

def run():
    print("--- 🔧 FINAL FIX: CREATING WORKFLOW DEPENDENCIES ---")

    # 1. STATES
    states = [
        ("Identified", "Inverse"),
        ("To Buy", "Inverse"),
        ("Buying", "Info"),
        ("Scanning", "Inverse"),
        ("Proposal", "Inverse"),
        ("Review", "Warning"),
        ("Approved", "Success"),
        ("Rejected", "Danger")
    ]
    
    for s_name, s_style in states:
        if not frappe.db.exists("Workflow State", s_name):
            try:
                # Try standard create
                d = frappe.get_doc({
                    "doctype": "Workflow State",
                    "workflow_state_name": s_name,
                    "style": s_style
                })
                d.name = s_name
                d.insert(ignore_permissions=True)
            except Exception:
                # Fallback SQL
                frappe.db.sql("""
                    INSERT INTO `tabWorkflow State` (name, workflow_state_name, style, modified, creation, owner, modified_by)
                    VALUES (%s, %s, %s, NOW(), NOW(), 'Administrator', 'Administrator')
                """, (s_name, s_name, s_style))
            print(f"✔ State Ready: {s_name}")

    # 2. ACTIONS (The problematic part)
    actions = ["Approve for Purchase", "Assign Buyer", "Upload Documents", "Start Proposal", "Submit for Review", "Approve Bid", "Reject Bid"]
    
    for a in actions:
        if not frappe.db.exists("Workflow Action", a):
            try:
                # Try standard create
                d = frappe.get_doc({
                    "doctype": "Workflow Action",
                    "workflow_action_name": a
                })
                d.name = a
                d.insert(ignore_permissions=True)
            except Exception:
                # Fallback SQL - using 'action' instead of 'workflow_action_name' if older schema
                # We try both common column names
                try:
                    frappe.db.sql("""
                        INSERT INTO `tabWorkflow Action` (name, workflow_action_name, modified, creation, owner, modified_by)
                        VALUES (%s, %s, NOW(), NOW(), 'Administrator', 'Administrator')
                    """, (a, a))
                except:
                    frappe.db.sql("""
                        INSERT INTO `tabWorkflow Action` (name, action, modified, creation, owner, modified_by)
                        VALUES (%s, %s, NOW(), NOW(), 'Administrator', 'Administrator')
                    """, (a, a))
            print(f"✔ Action Ready: {a}")

    frappe.db.commit()

    # 3. WORKFLOW
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
    print("--- ✅ SUCCESS: TENDER SYSTEM ONLINE ---")

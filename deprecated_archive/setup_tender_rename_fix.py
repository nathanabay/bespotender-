import frappe

def run():
    print("--- 🔧 FIXING ACTION NAMES (RENAMING) ---")

    actions = ["Approve for Purchase", "Assign Buyer", "Upload Documents", "Start Proposal", "Submit for Review", "Approve Bid", "Reject Bid"]

    # 1. Clean Slate for Actions
    # We delete existing ones to avoid confusion
    for a in actions:
        if frappe.db.exists("Workflow Action", a):
            continue # It already exists correctly
        
        # Check if it exists under a different ID
        # (We assume the field is either 'workflow_action_name' or 'action')
        existing = frappe.db.sql(f"SELECT name FROM `tabWorkflow Action` WHERE workflow_action_name='{a}'", as_dict=True)
        
        if existing:
            old_name = existing[0].name
            print(f"🔄 Renaming {old_name} -> {a}")
            frappe.rename_doc("Workflow Action", old_name, a, force=True)
        else:
            # Create it fresh
            d = frappe.get_doc({
                "doctype": "Workflow Action",
                "workflow_action_name": a
            })
            d.insert(ignore_permissions=True)
            
            # If it didn't get the right name, rename it immediately
            if d.name != a:
                print(f"🔄 Renaming New {d.name} -> {a}")
                frappe.rename_doc("Workflow Action", d.name, a, force=True)
    
    frappe.db.commit()
    print("✔ Actions Verified & Renamed")

    # 2. STATES (Ensure they exist)
    states = [
        ("Identified", "Inverse"), ("To Buy", "Inverse"), ("Buying", "Info"),
        ("Scanning", "Inverse"), ("Proposal", "Inverse"), ("Review", "Warning"),
        ("Approved", "Success"), ("Rejected", "Danger")
    ]
    for s_name, s_style in states:
        if not frappe.db.exists("Workflow State", s_name):
            d = frappe.get_doc({
                "doctype": "Workflow State",
                "workflow_state_name": s_name,
                "style": s_style
            })
            d.insert(ignore_permissions=True)
            if d.name != s_name:
                frappe.rename_doc("Workflow State", d.name, s_name, force=True)
    
    frappe.db.commit()
    print("✔ States Verified")

    # 3. INSTALL WORKFLOW
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
    print("--- ✅ FINAL SUCCESS: TENDER SYSTEM READY ---")

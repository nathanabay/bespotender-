import frappe

def run():
    print("--- ☢️ RUNNING DIRECT SQL WORKFLOW SETUP ---")

    # 1. DEFINE DATA
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
    
    actions = [
        "Approve for Purchase", "Assign Buyer", "Upload Documents", 
        "Start Proposal", "Submit for Review", "Approve Bid", "Reject Bid"
    ]

    # 2. FORCE INSERT STATES (SQL)
    print("... Writing States to Database")
    for s_name, s_style in states:
        # Check if exists to avoid duplicate error
        exists = frappe.db.sql("SELECT name FROM `tabWorkflow State` WHERE name=%s", (s_name,))
        if not exists:
            frappe.db.sql("""
                INSERT INTO `tabWorkflow State` 
                (name, workflow_state_name, style, creation, modified, modified_by, owner, docstatus)
                VALUES (%s, %s, %s, NOW(), NOW(), 'Administrator', 'Administrator', 0)
            """, (s_name, s_name, s_style))
            print(f"✔ Forced State: {s_name}")

    # 3. FORCE INSERT ACTIONS (SQL)
    print("... Writing Actions to Database")
    for a_name in actions:
        exists = frappe.db.sql("SELECT name FROM `tabWorkflow Action` WHERE name=%s", (a_name,))
        if not exists:
            frappe.db.sql("""
                INSERT INTO `tabWorkflow Action` 
                (name, workflow_action_name, creation, modified, modified_by, owner, docstatus)
                VALUES (%s, %s, NOW(), NOW(), 'Administrator', 'Administrator', 0)
            """, (a_name, a_name))
            print(f"✔ Forced Action: {a_name}")

    frappe.db.commit() # Save SQL changes immediately
    frappe.clear_cache() # Make sure ERPNext sees the new SQL data

    # 4. CREATE WORKFLOW (Standard ORM)
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
    
    print("--- ✅ DONE: WORKFLOW INSTALLED AND LINKED ---")

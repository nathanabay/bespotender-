import frappe

def run():
    print("--- 👮 SETTING UP 2-STAGE APPROVAL WORKFLOW (FIXED V3) ---")

    # 1. CREATE REQUIRED ROLES
    roles = ["Tender User", "Tender Manager", "Tender Director"]
    for r in roles:
        if not frappe.db.exists("Role", r):
            frappe.get_doc({"doctype": "Role", "role_name": r}).insert(ignore_permissions=True)
            print(f"✔ Created Role: {r}")

    # 2. CREATE WORKFLOW ACTIONS (THE MISSING STEP)
    # These are the buttons users will click
    actions = ["Submit for Review", "Approve (Level 1)", "Approve (Final)", "Reject", "Restart"]
    for act in actions:
        if not frappe.db.exists("Workflow Action Master", act):
            frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": act}).insert(ignore_permissions=True)
            print(f"✔ Created Action: {act}")

    # 3. DEFINE WORKFLOW STATES
    states = [
        {"state": "Draft", "doc_status": 0, "allow_edit": "Tender User", "style": "Inverse"},
        {"state": "Pending Review", "doc_status": 0, "allow_edit": "Tender Manager", "style": "Warning"},
        {"state": "Pending Final Approval", "doc_status": 0, "allow_edit": "Tender Director", "style": "Primary"},
        {"state": "Approved to Bid", "doc_status": 1, "allow_edit": "", "style": "Success"},
        {"state": "Rejected", "doc_status": 2, "allow_edit": "", "style": "Danger"}
    ]
    
    for s in states:
        if not frappe.db.exists("Workflow State", s["state"]):
            frappe.get_doc({
                "doctype": "Workflow State",
                "workflow_state_name": s["state"],
                "style": s["style"]
            }).insert(ignore_permissions=True)

    # 4. CREATE THE WORKFLOW DOCUMENT
    wf_name = "Two-Stage Tender Approval"
    
    if frappe.db.exists("Workflow", wf_name):
        frappe.delete_doc("Workflow", wf_name)

    wf = frappe.get_doc({
        "doctype": "Workflow",
        "workflow_name": wf_name,
        "document_type": "Tender Opportunity",
        "is_active": 1,
        "workflow_state_field": "workflow_state",
        "states": states,
        "transitions": [
            {
                "state": "Draft",
                "action": "Submit for Review",
                "next_state": "Pending Review",
                "allowed": "Tender User"
            },
            {
                "state": "Pending Review",
                "action": "Approve (Level 1)",
                "next_state": "Pending Final Approval",
                "allowed": "Tender Manager"
            },
            {
                "state": "Pending Final Approval",
                "action": "Approve (Final)",
                "next_state": "Approved to Bid",
                "allowed": "Tender Director"
            },
            {
                "state": "Pending Review",
                "action": "Reject",
                "next_state": "Rejected",
                "allowed": "Tender Manager"
            },
            {
                "state": "Pending Final Approval",
                "action": "Reject",
                "next_state": "Rejected",
                "allowed": "Tender Director"
            },
            {
                "state": "Rejected",
                "action": "Restart",
                "next_state": "Draft",
                "allowed": "Tender User"
            }
        ]
    })
    
    wf.insert(ignore_permissions=True)
    print("--- ✅ WORKFLOW ACTIVATED ---")

if __name__ == "__main__":
    run()

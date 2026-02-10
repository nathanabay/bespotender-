import frappe

def run():
    print("--- 👮 SETTING UP 2-STAGE APPROVAL WORKFLOW ---")

    # 1. CREATE REQUIRED ROLES
    # We need specific hats for people to wear
    roles = ["Tender User", "Tender Manager", "Tender Director"]
    for r in roles:
        if not frappe.db.exists("Role", r):
            frappe.get_doc({"doctype": "Role", "role_name": r}).insert(ignore_permissions=True)
            print(f"✔ Created Role: {r}")

    # 2. DEFINE WORKFLOW STATES
    states = [
        {"state": "Draft", "doc_status": 0, "allow_edit": "Tender User", "style": "Gray"},
        {"state": "Pending Review", "doc_status": 0, "allow_edit": "Tender Manager", "style": "Orange"},
        {"state": "Pending Final Approval", "doc_status": 0, "allow_edit": "Tender Director", "style": "Blue"},
        {"state": "Approved to Bid", "doc_status": 1, "allow_edit": "", "style": "Green"}, # Submitted
        {"state": "Rejected", "doc_status": 2, "allow_edit": "", "style": "Red"} # Cancelled
    ]
    
    for s in states:
        if not frappe.db.exists("Workflow State", s["state"]):
            frappe.get_doc({
                "doctype": "Workflow State",
                "workflow_state_name": s["state"],
                "style": s["style"]
            }).insert(ignore_permissions=True)

    # 3. CREATE THE WORKFLOW DOCUMENT
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
            # User submits to Manager
            {
                "state": "Draft",
                "action": "Submit for Review",
                "next_state": "Pending Review",
                "allowed": "Tender User"
            },
            # Manager approves to Director
            {
                "state": "Pending Review",
                "action": "Approve (Level 1)",
                "next_state": "Pending Final Approval",
                "allowed": "Tender Manager"
            },
            # Director gives final Go-Ahead
            {
                "state": "Pending Final Approval",
                "action": "Approve (Final)",
                "next_state": "Approved to Bid",
                "allowed": "Tender Director"
            },
            # Rejections
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
            # Restart
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
    print("👉 NOTE: Go to 'User List' and assign 'Tender Manager' and 'Tender Director' roles to the correct people.")

if __name__ == "__main__":
    run()

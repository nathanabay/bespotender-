import frappe

def run():
    print("--- 🏗 STEP 1: CREATING WORKFLOW STATES & ACTIONS ---")

    states = ["Identified", "To Buy", "Buying", "Scanning", "Proposal", "Review", "Approved", "Rejected"]
    actions = ["Approve for Purchase", "Assign Buyer", "Upload Documents", "Start Proposal", "Submit for Review", "Approve Bid", "Reject Bid"]

    # 1. Create States
    for s in states:
        if not frappe.db.exists("Workflow State", s):
            style = "Inverse"
            if s == "Approved": style = "Success"
            elif s == "Rejected": style = "Danger"
            elif s == "Review": style = "Warning"
            elif s == "Buying": style = "Info"

            d = frappe.get_doc({
                "doctype": "Workflow State",
                "workflow_state_name": s,
                "name": s, # Force ID to match name
                "style": style
            })
            d.insert(ignore_permissions=True)
            print(f"✔ Created State: {s}")

    # 2. Create Actions
    for a in actions:
        if not frappe.db.exists("Workflow Action", a):
            d = frappe.get_doc({
                "doctype": "Workflow Action",
                "workflow_action_name": a,
                "name": a # Force ID to match name
            })
            d.insert(ignore_permissions=True)
            print(f"✔ Created Action: {a}")

    frappe.db.commit()
    print("--- ✅ DEPENDENCIES CREATED ---")

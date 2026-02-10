import frappe

def run():
    print("--- 🔧 REPAIRING WORKFLOW ACTIONS ---")

    # 1. DEFINE THE REQUIRED ACTIONS
    # These must match the Workflow transitions EXACTLY
    required_actions = [
        "Submit for Review",
        "Approve (Level 1)",
        "Approve (Final)",
        "Reject",
        "Restart"
    ]

    # 2. ENSURE THEY EXIST IN THE DATABASE
    for action in required_actions:
        if not frappe.db.exists("Workflow Action Master", action):
            try:
                doc = frappe.get_doc({
                    "doctype": "Workflow Action Master",
                    "workflow_action_name": action
                })
                doc.insert(ignore_permissions=True)
                print(f"✔ Created Missing Action: {action}")
            except Exception as e:
                print(f"⚠ Could not create '{action}': {str(e)}")
        else:
            print(f"✔ Verified: {action}")

    frappe.db.commit() # Force save to DB

    # 3. RELOAD THE WORKFLOW TO SYNC
    wf_name = "Two-Stage Tender Approval"
    if frappe.db.exists("Workflow", wf_name):
        doc = frappe.get_doc("Workflow", wf_name)
        doc.save(ignore_permissions=True)
        print("✔ Synced Workflow with Actions")
    
    print("--- ✅ REPAIR COMPLETE ---")

if __name__ == "__main__":
    run()

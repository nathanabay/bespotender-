import frappe
from frappe.utils import add_days, nowdate
import json
import random

def run():
    print("--- 🔫 RUNNING SILVER BULLET FIX ---")

    # ==============================================================================
    # 1. CRITICAL FIX: UPDATE STATUS OPTIONS
    # ==============================================================================
    # The system was rejecting "Draft" because it wasn't in the list. We force it in.
    new_states = "Draft\nUnder Evaluation\nApproved to Bid\nTender Purchased\nBid Bond Issued\nTechnical Preparation\nFinancial Preparation\nReady for Submission\nSubmitted\nUnder Client Evaluation\nWon\nLost"
    
    doc = frappe.get_doc("DocType", "Tender Opportunity")
    updated = False
    for field in doc.fields:
        if field.fieldname == "workflow_state":
            field.options = new_states
            updated = True
            break
    
    if updated:
        doc.save(ignore_permissions=True)
        print("✔ Fixed: 'workflow_state' options updated to SOP values")
    else:
        print("⚠️ Warning: Could not find 'workflow_state' field")

    frappe.db.commit() # Commit schema change immediately

    # ==============================================================================
    # 2. ENSURE ACTIONS EXIST
    # ==============================================================================
    actions = ["Start Evaluation", "Approve Go", "Confirm Purchase", "Issue Bond", "Start Technical", "Start Financial", "Finalize", "Submit Bid", "Client Review", "Award Tender", "Regret"]
    for a in actions:
        if not frappe.db.exists("Workflow Action", a):
            frappe.db.sql("INSERT INTO `tabWorkflow Action` (name, creation, modified) VALUES (%s, NOW(), NOW())", (a,))
    print("✔ Actions Verified")

    # ==============================================================================
    # 3. GENERATE SAMPLE DATA (Now that options are fixed)
    # ==============================================================================
    tenders = [
        {"title": "HQ Office Construction (Sample)", "sector": "Construction", "state": "Submitted", "price": 15000000, "bond": "CPO", "b_amt": 150000, "deadline": 2},
        {"title": "Generator Supply 500kVA (Sample)", "sector": "Electro-Mechanical", "state": "Won", "price": 4500000, "bond": "Bank Guarantee", "b_amt": 45000, "deadline": -10},
        {"title": "Rural Road Project (Sample)", "sector": "Construction", "state": "Lost", "price": 22000000, "bond": "Insurance Bond", "b_amt": 220000, "deadline": -25},
        {"title": "HVAC Maintenance (Sample)", "sector": "Electro-Mechanical", "state": "Draft", "price": 850000, "bond": "CPO", "b_amt": 8500, "deadline": 5}
    ]

    print("... Creating Data")
    for t in tenders:
        if not frappe.db.exists("Tender Opportunity", {"title": t["title"]}):
            new_doc = frappe.get_doc({
                "doctype": "Tender Opportunity",
                "tender_number": f"T-{random.randint(1000,9999)}",
                "title": t["title"],
                "sector": t["sector"],
                "workflow_state": "Draft", # Start valid
                "final_bid_price": t["price"],
                "bond_type": t["bond"],
                "bond_amount": t["b_amt"],
                "deadline": add_days(nowdate(), t["deadline"])
            })
            new_doc.insert(ignore_permissions=True)
            
            # Move to final state
            if t["state"] != "Draft":
                frappe.db.set_value("Tender Opportunity", new_doc.name, "workflow_state", t["state"])
            
            print(f"✔ Created: {t['title']}")

    # ==============================================================================
    # 4. REBUILD DASHBOARD
    # ==============================================================================
    ws_name = "Tender Management"
    if frappe.db.exists("Workspace", ws_name):
        frappe.delete_doc("Workspace", ws_name, force=True)

    ws_content = [
        {"type": "header", "data": {"text": "Tender Performance (SOP)", "level": 2}},
        {"type": "chart", "data": {"chart_name": "SOP Total Bid Value", "col": 12}},
        {"type": "chart", "data": {"chart_name": "SOP Win Ratio", "col": 6}},
        {"type": "chart", "data": {"chart_name": "SOP Bond Exposure", "col": 6}},
        {"type": "header", "data": {"text": "Process Links", "level": 2}},
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "label": "Tender Registry", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "label": "Bond Tracking", "icon": "lock", "color": "Orange"}},
        {
            "type": "shortcut", 
            "data": {
                "link_to": "Tender Opportunity", 
                "label": "Deadlines This Week", 
                "icon": "calendar", 
                "color": "Red",
                "stats_filter": json.dumps({"deadline": ["Timespan", "This Week"]})
            }
        }
    ]

    frappe.get_doc({
        "doctype": "Workspace",
        "name": ws_name,
        "label": ws_name,
        "title": ws_name,
        "category": "Modules",
        "module": "Tender Management",
        "public": 1,
        "content": json.dumps(ws_content)
    }).insert(ignore_permissions=True)

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ SUCCESS! REPAIR COMPLETE ---")

if __name__ == "__main__":
    run()

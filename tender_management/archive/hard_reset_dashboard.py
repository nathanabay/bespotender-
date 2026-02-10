import frappe
from frappe.utils import add_days, nowdate
import json
import random

def run():
    print("--- 🛠 STARTING HARD RESET & REPAIR ---")

    # 1. FIX THE DOCTYPE OPTIONS (Crucial Step)
    # This fixes the "ValidationError: Status cannot be Draft" error
    try:
        doc = frappe.get_doc("DocType", "Tender Opportunity")
        new_options = "Draft\nUnder Evaluation\nApproved to Bid\nTender Purchased\nBid Bond Issued\nTechnical Preparation\nFinancial Preparation\nReady for Submission\nSubmitted\nUnder Client Evaluation\nWon\nLost"
        
        for field in doc.fields:
            if field.fieldname == "workflow_state":
                field.options = new_options
                break
        
        doc.save(ignore_permissions=True)
        print("✔ Fixed 'workflow_state' options.")
    except Exception as e:
        print(f"⚠️ DocType update skipped (might already be correct): {e}")

    # 2. CLEAR OLD SAMPLE DATA
    frappe.db.sql("DELETE FROM `tabTender Opportunity` WHERE tender_number LIKE 'T-2026-%'")
    print("✔ Cleared old sample data.")

    # 3. GENERATE FRESH SAMPLE DATA
    # We create them as 'Draft' first, then force the status.
    tenders = [
        {"title": "HQ Construction (Sample)", "sector": "Construction", "state": "Submitted", "price": 15000000, "bond": "CPO", "b_amt": 150000, "deadline": 2},
        {"title": "Generator Supply (Sample)", "sector": "Electro-Mechanical", "state": "Won", "price": 4500000, "bond": "Bank Guarantee", "b_amt": 45000, "deadline": -10},
        {"title": "Rural Road Project (Sample)", "sector": "Construction", "state": "Lost", "price": 22000000, "bond": "Insurance Bond", "b_amt": 220000, "deadline": -25},
        {"title": "HVAC Maintenance (Sample)", "sector": "Electro-Mechanical", "state": "Draft", "price": 850000, "bond": "CPO", "b_amt": 8500, "deadline": 5}
    ]

    print("... Generating 4 new records")
    for t in tenders:
        new_doc = frappe.get_doc({
            "doctype": "Tender Opportunity",
            "tender_number": f"T-2026-{random.randint(1000,9999)}",
            "title": t["title"],
            "sector": t["sector"],
            "workflow_state": "Draft", 
            "final_bid_price": t["price"],
            "bond_type": t["bond"],
            "bond_amount": t["b_amt"],
            "deadline": add_days(nowdate(), t["deadline"])
        })
        new_doc.insert(ignore_permissions=True)
        
        # Force status update directly in DB
        frappe.db.set_value("Tender Opportunity", new_doc.name, "workflow_state", t["state"])

    # 4. REBUILD WORKSPACE
    ws_name = "Tender Management"
    if frappe.db.exists("Workspace", ws_name):
        frappe.delete_doc("Workspace", ws_name, force=True)

    # Clean up any "private" user-customized versions that show up blank
    frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name = %s AND public = 0", (ws_name,))

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
    print("--- ✅ REPAIR COMPLETE: PLEASE RELOAD ---")

if __name__ == "__main__":
    run()

import frappe
import json
from frappe.utils import add_days, nowdate

def run():
    print("--- 🔧 FIXING DASHBOARD & DATA ---")

    # 1. GENERATE TEST DATA (Crucial for Charts/Reports to work)
    # If we don't have data, the "Win Rate" calculation divides by zero and crashes.
    if frappe.db.count("Tender Opportunity") < 3:
        print("... Generating Test Data")
        
        # 1. A Won Tender
        frappe.get_doc({
            "doctype": "Tender Opportunity",
            "title": "Headquarters Construction (Won)",
            "sector": "Construction",
            "status": "Closed",
            "workflow_state": "Won",
            "submission_deadline": add_days(nowdate(), -30),
            "final_bid_price": 50000000,
            "estimated_cost": 40000000 # 20% Margin
        }).insert(ignore_permissions=True)

        # 2. A Lost Tender
        frappe.get_doc({
            "doctype": "Tender Opportunity",
            "title": "Road Maintenance (Lost)",
            "sector": "Maintenance",
            "status": "Closed",
            "workflow_state": "Lost",
            "submission_deadline": add_days(nowdate(), -15),
            "final_bid_price": 12000000
        }).insert(ignore_permissions=True)

        # 3. An Active Tender
        frappe.get_doc({
            "doctype": "Tender Opportunity",
            "title": "Water Works Phase 3",
            "sector": "Water Works",
            "status": "Open",
            "workflow_state": "Submitted",
            "submission_deadline": add_days(nowdate(), 10),
            "final_bid_price": 25000000
        }).insert(ignore_permissions=True)
        print("✔ Created 3 Test Tenders (Won, Lost, Active)")

    # 2. CREATE A STABLE WORKSPACE
    # We remove the "Chart" widget for now (since it causes the Sad Face) and replace it with direct links.
    ws_name = "Tender Management"
    
    ws_content = [
        {"type": "header", "data": {"text": "Tender Strategy", "level": 1}},
        
        # Link to the POWERFUL REPORT we just made
        {"type": "shortcut", "data": {"link_to": "Strategic Tender Analytics", "type": "Report", "label": "Open Strategic Analytics", "icon": "line-chart", "color": "Green"}},
        
        {"type": "header", "data": {"text": "Daily Operations", "level": 2}},
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "type": "DocType", "label": "Tender List", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Tender Bid", "type": "DocType", "label": "Bids", "icon": "file-text", "color": "Purple"}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "type": "DocType", "label": "Bid Bonds", "icon": "lock", "color": "Orange"}}
    ]

    # Force Overwrite
    if frappe.db.exists("Workspace", ws_name):
        doc = frappe.get_doc("Workspace", ws_name)
        doc.content = json.dumps(ws_content)
        doc.save(ignore_permissions=True)
    
    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ WORKSPACE REPAIRED ---")

if __name__ == "__main__":
    run()

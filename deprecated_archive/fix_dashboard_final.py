import frappe
import json
from frappe.utils import nowdate

def run():
    print("--- 🔧 FINAL DASHBOARD REPAIR ---")

    # 1. ENSURE DATA EXISTS (Crucial for Charts)
    if frappe.db.count("Tender Opportunity") == 0:
        frappe.get_doc({
            "doctype": "Tender Opportunity",
            "title": "System Test Tender",
            "sector": "Construction",
            "tender_number": "TEST-001",
            "status": "Open",
            "workflow_state": "Draft",
            "submission_deadline": nowdate(),
            "final_bid_price": 100000
        }).insert(ignore_permissions=True)
        print("✔ Created Dummy Tender (to prevent empty chart crash)")
    else:
        print("✔ Data found (Charts should have data)")

    # 2. CREATE A ROBUST NUMBER CARD (Green Box)
    # This acts as a backup. If the chart fails, this should still show.
    card_name = "Total Tenders KPI"
    if not frappe.db.exists("Number Card", card_name):
        frappe.get_doc({
            "doctype": "Number Card",
            "name": card_name,
            "label": "Total Active Tenders",
            "function": "Count",
            "document_type": "Tender Opportunity",
            "is_public": 1,
            "color": "#2ecc71", # Green
            "filters_json": "[]"
        }).insert(ignore_permissions=True)
    print("✔ Created Number Card: Total Active Tenders")

    # 3. CREATE A SIMPLE BAR CHART
    chart_name = "Tender Status Bar"
    
    # Delete old versions to be safe
    if frappe.db.exists("Dashboard Chart", chart_name):
        frappe.delete_doc("Dashboard Chart", chart_name, force=True)

    frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": chart_name,
        "chart_type": "Group By",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "workflow_state", 
        "type": "Bar",
        "timeseries": 0,
        "is_public": 1,
        "color": "#3498db", # Blue
        "filters_json": "[]"
    }).insert(ignore_permissions=True)
    print("✔ Created Chart: Tender Status Bar")

    # 4. UPDATE WORKSPACE
    ws_name = "Tender Management"
    ws_content = [
        {"type": "header", "data": {"text": "Dashboard", "level": 2}},
        
        # Row 1: The Number Card (Should always work)
        {"type": "card", "data": {"card_name": card_name, "col": 4}},
        
        # Row 2: The Bar Chart
        {"type": "chart", "data": {"chart_name": chart_name, "col": 12}},

        {"type": "header", "data": {"text": "Quick Actions", "level": 2}},
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "type": "DocType", "label": "Tender Registry", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "type": "DocType", "label": "Bid Bonds", "icon": "lock", "color": "Orange"}}
    ]

    # Force update the workspace
    if frappe.db.exists("Workspace", ws_name):
        doc = frappe.get_doc("Workspace", ws_name)
        doc.content = json.dumps(ws_content)
        doc.save(ignore_permissions=True)
    
    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ DASHBOARD REPAIRED ---")

if __name__ == "__main__":
    run()

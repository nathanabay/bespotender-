import frappe
import json

def run():
    print("--- 🗑️ DELETING OLD CHARTS & RECREATING FRESH ---")

    # 1. DELETE ALL PREVIOUS CHARTS (Clean Slate)
    # We remove every chart we might have created to ensure no conflicts.
    charts_to_delete = [
        "SOP Total Bid Value", 
        "Strategic Bid Funnel", 
        "Win Volume by Sector", 
        "Tender Pipeline Trend", 
        "Tender Status Bar", 
        "Tender Status Breakdown", 
        "Total Tenders Test",
        "Chart Funnel"
    ]
    
    for chart in charts_to_delete:
        if frappe.db.exists("Dashboard Chart", chart):
            frappe.delete_doc("Dashboard Chart", chart, force=True)
            print(f"   ✂️ Deleted: {chart}")

    # 2. CREATE NEW CHART 1: TENDERS BY STATUS (Bar Chart)
    # Simple count of tenders in each stage (Draft, Submitted, Won, etc.)
    chart_1 = "Tender Status Overview"
    frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": chart_1,
        "chart_type": "Group By",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "workflow_state", 
        "type": "Bar",
        "timeseries": 0,
        "is_public": 1,
        "color": "#3498db", # Blue
        "filters_json": "[]" # Empty filter required for validation
    }).insert(ignore_permissions=True)
    print(f"✔ Created Chart: {chart_1}")

    # 3. CREATE NEW CHART 2: VALUE BY SECTOR (Donut Chart)
    # Sum of Final Bid Price grouped by Sector (Construction vs Water vs etc.)
    chart_2 = "Bid Value by Sector"
    frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": chart_2,
        "chart_type": "Group By",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "sector",
        "aggregate_function_based_on": "final_bid_price",
        "aggregate_function": "Sum",
        "type": "Donut",
        "timeseries": 0,
        "is_public": 1,
        "filters_json": "[]"
    }).insert(ignore_permissions=True)
    print(f"✔ Created Chart: {chart_2}")

    # 4. UPDATE WORKSPACE
    ws_name = "Tender Management"
    
    ws_content = [
        {"type": "header", "data": {"text": "Tender Dashboard", "level": 1}},
        
        # Row 1: The Two New Charts
        {"type": "chart", "data": {"chart_name": chart_1, "col": 8}},
        {"type": "chart", "data": {"chart_name": chart_2, "col": 4}},

        {"type": "header", "data": {"text": "Registers", "level": 2}},
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "type": "DocType", "label": "All Tenders", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Tender Bid", "type": "DocType", "label": "Bids", "icon": "file-text", "color": "Purple"}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "type": "DocType", "label": "Bid Bonds", "icon": "lock", "color": "Orange"}},
        
        {"type": "header", "data": {"text": "Analytics", "level": 2}},
        {"type": "shortcut", "data": {"link_to": "Strategic Tender Analytics", "type": "Report", "label": "Detailed Analytics Report", "icon": "line-chart", "color": "Green"}}
    ]

    if frappe.db.exists("Workspace", ws_name):
        doc = frappe.get_doc("Workspace", ws_name)
        doc.content = json.dumps(ws_content)
        doc.save(ignore_permissions=True)

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ FRESH CHARTS DEPLOYED ---")

if __name__ == "__main__":
    run()

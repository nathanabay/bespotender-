import frappe
import json

def run():
    print("--- 📊 FIXING CHART RENDERING ---")

    ws_name = "Tender Management"
    chart_name = "Tender Status Breakdown"

    # 1. DELETE OLD FAILED CHART
    frappe.db.sql("DELETE FROM `tabDashboard Chart` WHERE chart_name = %s", ("Total Tenders Test",))
    if frappe.db.exists("Dashboard Chart", chart_name):
        frappe.delete_doc("Dashboard Chart", chart_name, force=True)

    # 2. CREATE A ROBUST DONUT CHART
    # Donut charts are the easiest for the system to render.
    # We use a filter that matches ALL non-deleted records.
    frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": chart_name,
        "chart_type": "Group By",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "workflow_state", 
        "type": "Donut", 
        "is_public": 1,
        "timeseries": 0,
        "color": "#2ecc71",
        "filters_json": json.dumps([["Tender Opportunity", "name", "is", "set"]]) # "Get Everything" Filter
    }).insert(ignore_permissions=True)
    print("✔ Created 'Tender Status Breakdown' Chart")

    # 3. UPDATE WORKSPACE
    ws_content = [
        {"type": "header", "data": {"text": "Tender Console", "level": 2}},
        
        # The New Donut Chart
        {"type": "chart", "data": {"chart_name": chart_name, "col": 12}},

        {"type": "header", "data": {"text": "Quick Actions", "level": 2}},
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "type": "DocType", "label": "Tender Registry", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Tender Bid", "type": "DocType", "label": "Bids", "icon": "users", "color": "Purple"}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "type": "DocType", "label": "Bid Bonds", "icon": "lock", "color": "Orange"}}
    ]

    doc = frappe.get_doc("Workspace", ws_name)
    doc.content = json.dumps(ws_content)
    doc.save(ignore_permissions=True)
    print("✔ Workspace Updated with Donut Chart")

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ CHART FIXED ---")

if __name__ == "__main__":
    run()

import frappe
import json

def run():
    print("--- 📊 CREATING TENDER ANALYTICS DASHBOARD ---")

    # 1. Pipeline Value Chart
    chart_1 = "Tender Pipeline Value"
    if frappe.db.exists("Dashboard Chart", chart_1):
        frappe.delete_doc("Dashboard Chart", chart_1)
        
    frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": chart_1,
        "chart_type": "Group By",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "workflow_state",
        "aggregate_function_based_on": "total_bid_value",
        "aggregate_function": "Sum",
        "type": "Bar",
        "timeseries": 0,
        "is_public": 1,
        "filters_json": "[]"
    }).insert(ignore_permissions=True)
    print(f"✔ Chart Created: {chart_1}")

    # 2. Win Loss Ratio Chart
    chart_2 = "Win Loss Ratio"
    if frappe.db.exists("Dashboard Chart", chart_2):
        frappe.delete_doc("Dashboard Chart", chart_2)

    frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": chart_2,
        "chart_type": "Count",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "workflow_state",
        "based_on": "creation",
        "timeseries": 0,
        "filters_json": json.dumps([["Tender Opportunity", "workflow_state", "in", ["Approved", "Rejected"]]]),
        "type": "Donut",
        "is_public": 1
    }).insert(ignore_permissions=True)
    print(f"✔ Chart Created: {chart_2}")

    # 3. Workspace
    workspace_name = "Tender Management"
    if frappe.db.exists("Workspace", workspace_name):
        frappe.delete_doc("Workspace", workspace_name)

    ws_content = [
        {"type": "header", "data": {"text": "Tender Performance Overview", "level": 2}},
        {"type": "chart", "data": {"chart_name": chart_1, "col": 8}},
        {"type": "chart", "data": {"chart_name": chart_2, "col": 4}},
        {"type": "header", "data": {"text": "Quick Links", "level": 3}},
        {"type": "link", "data": {"link_to": "Tender Opportunity", "link_type": "DocType", "label": "Active Tenders"}},
        {"type": "link", "data": {"link_to": "Bid Security", "link_type": "DocType", "label": "CPO Tracking"}}
    ]
    
    frappe.get_doc({
        "doctype": "Workspace",
        "name": workspace_name,
        "label": workspace_name,
        "title": workspace_name,
        "category": "Modules",
        "module": "Tender Management",
        "icon": "folder",
        "public": 1,
        "content": json.dumps(ws_content)
    }).insert(ignore_permissions=True)
    print(f"✔ Workspace Created: {workspace_name}")

    frappe.db.commit()
    print("--- ✅ DASHBOARD SETUP SUCCESSFULLY COMPLETED ---")

if __name__ == "__main__":
    run()

import frappe
import json

def run():
    print("--- ☢️ INITIATING NUCLEAR DASHBOARD RESET (FIXED) ---")

    ws_name = "Tender Management"
    
    # 1. DELETE EVERYTHING
    frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name = %s", (ws_name,))
    
    charts = ["Strategic Bid Funnel", "Win Volume by Sector"]
    cards = ["Tenders Won", "Total Pipeline Value", "Bids Due Soon"]
    
    for c in charts:
        if frappe.db.exists("Dashboard Chart", c):
            frappe.delete_doc("Dashboard Chart", c, force=True)
            
    for c in cards:
        if frappe.db.exists("Number Card", c):
            frappe.delete_doc("Number Card", c, force=True)

    print("✔ Cleared old Dashboard components")

    # 2. RECREATE NUMBER CARDS
    frappe.get_doc({
        "doctype": "Number Card",
        "name": "Tenders Won",
        "label": "Total Wins",
        "function": "Count",
        "document_type": "Tender Opportunity",
        "filters_json": json.dumps([["Tender Opportunity", "workflow_state", "=", "Won"]]),
        "color": "#2ecc71"
    }).insert(ignore_permissions=True)

    frappe.get_doc({
        "doctype": "Number Card",
        "name": "Total Pipeline Value",
        "label": "Active Pipeline",
        "function": "Sum",
        "aggregate_function_based_on": "final_bid_price",
        "document_type": "Tender Opportunity",
        "filters_json": json.dumps([["Tender Opportunity", "workflow_state", "in", ["Submitted", "Approved to Bid"]]]),
        "color": "#3498db"
    }).insert(ignore_permissions=True)

    frappe.get_doc({
        "doctype": "Number Card",
        "name": "Bids Due Soon",
        "label": "Due This Week",
        "function": "Count",
        "document_type": "Tender Opportunity",
        "filters_json": json.dumps([["Tender Opportunity", "submission_deadline", "Timespan", "This Week"]]),
        "color": "#e74c3c"
    }).insert(ignore_permissions=True)

    # 3. RECREATE CHARTS (With Filters Fixed)
    frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": "Strategic Bid Funnel",
        "chart_type": "Group By",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "workflow_state", 
        "type": "Bar",
        "timeseries": 0,
        "is_public": 1,
        "color": "#9b59b6",
        # FIXED: Added filters_json
        "filters_json": json.dumps([["Tender Opportunity", "workflow_state", "in", ["Draft", "Approved to Bid", "Submitted", "Won", "Lost"]]])
    }).insert(ignore_permissions=True)

    frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": "Win Volume by Sector",
        "chart_type": "Group By",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "sector", 
        "aggregate_function_based_on": "final_bid_price",
        "aggregate_function": "Sum",
        "type": "Donut",
        "timeseries": 0,
        "is_public": 1,
        # FIXED: Added filters_json
        "filters_json": json.dumps([["Tender Opportunity", "workflow_state", "=", "Won"]])
    }).insert(ignore_permissions=True)

    # 4. REBUILD WORKSPACE
    ws_content = [
        {"type": "header", "data": {"text": "Strategic Dashboard", "level": 2}},
        {"type": "card", "data": {"card_name": "Tenders Won", "col": 4}},
        {"type": "card", "data": {"card_name": "Total Pipeline Value", "col": 4}},
        {"type": "card", "data": {"card_name": "Bids Due Soon", "col": 4}},
        {"type": "header", "data": {"text": "Analytics", "level": 2}},
        {"type": "chart", "data": {"chart_name": "Strategic Bid Funnel", "col": 8}},
        {"type": "chart", "data": {"chart_name": "Win Volume by Sector", "col": 4}},
        {"type": "header", "data": {"text": "Quick Links", "level": 2}},
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "type": "DocType", "label": "All Tenders", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Tender Content Library", "type": "DocType", "label": "Knowledge Base", "icon": "book", "color": "Teal"}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "type": "DocType", "label": "Bond Tracking", "icon": "lock", "color": "Orange"}}
    ]

    doc = frappe.get_doc({
        "doctype": "Workspace",
        "name": ws_name,
        "label": ws_name,
        "title": ws_name,
        "module": "Tender Management",
        "public": 1,
        "is_standard": 0,
        "content": json.dumps(ws_content)
    })
    doc.insert(ignore_permissions=True)

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ DASHBOARD RESET COMPLETE ---")

if __name__ == "__main__":
    run()

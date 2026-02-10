import frappe
import json

def run():
    print("--- 📊 INSTALLING STRATEGIC DASHBOARD (RESPONSIVE.IO MODEL) ---")

    # ==============================================================================
    # 1. CREATE NUMBER CARDS (KPIs)
    # ==============================================================================
    # KPI 1: Win Rate %
    if not frappe.db.exists("Number Card", "Tender Win Rate"):
        frappe.get_doc({
            "doctype": "Number Card",
            "name": "Tender Win Rate",
            "label": "Win Rate",
            "function": "Percentage",
            "document_type": "Tender Opportunity",
            "filters_json": json.dumps([["Tender Opportunity", "workflow_state", "=", "Won"]]),
            "aggregate_function_based_on": "name", # Count total won
            "color": "#2ecc71" # Green
        }).insert(ignore_permissions=True)
    
    # KPI 2: Total Pipeline Value
    if not frappe.db.exists("Number Card", "Total Pipeline Value"):
        frappe.get_doc({
            "doctype": "Number Card",
            "name": "Total Pipeline Value",
            "label": "Active Pipeline",
            "function": "Sum",
            "aggregate_function_based_on": "final_bid_price",
            "document_type": "Tender Opportunity",
            "filters_json": json.dumps([["Tender Opportunity", "workflow_state", "in", ["Submitted", "Approved to Bid", "Technical Preparation"]]]),
            "color": "#3498db" # Blue
        }).insert(ignore_permissions=True)

    # KPI 3: Bids Due Soon
    if not frappe.db.exists("Number Card", "Bids Due Soon"):
        frappe.get_doc({
            "doctype": "Number Card",
            "name": "Bids Due Soon",
            "label": "Closing This Week",
            "function": "Count",
            "document_type": "Tender Opportunity",
            "filters_json": json.dumps([["Tender Opportunity", "submission_deadline", "Timespan", "This Week"]]),
            "color": "#e74c3c" # Red
        }).insert(ignore_permissions=True)

    print("✔ Created KPI Cards: Win Rate, Pipeline, Deadlines")

    # ==============================================================================
    # 2. CREATE STRATEGIC CHARTS
    # ==============================================================================
    
    # Chart 1: The "Bid Funnel" (Identify -> Qualify -> Submit -> Win)
    # This visualizes the "Go/No-Go" process described in the blog.
    chart_funnel = "Strategic Bid Funnel"
    if frappe.db.exists("Dashboard Chart", chart_funnel):
        frappe.delete_doc("Dashboard Chart", chart_funnel)
        
    frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": chart_funnel,
        "chart_type": "Group By",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "workflow_state", 
        "type": "Bar",
        "timeseries": 0,
        "is_public": 1,
        "color": "#9b59b6",
        # We want to see volume at each stage
        "filters_json": json.dumps([["Tender Opportunity", "workflow_state", "in", ["Draft", "Approved to Bid", "Submitted", "Won"]]])
    }).insert(ignore_permissions=True)
    print("✔ Created Chart: Strategic Bid Funnel")

    # Chart 2: Win Rate by Sector (Where do we win?)
    chart_sector = "Win Volume by Sector"
    if frappe.db.exists("Dashboard Chart", chart_sector):
        frappe.delete_doc("Dashboard Chart", chart_sector)

    frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": chart_sector,
        "chart_type": "Group By",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "sector", 
        "aggregate_function_based_on": "final_bid_price",
        "aggregate_function": "Sum",
        "type": "Donut",
        "timeseries": 0,
        "is_public": 1,
        "filters_json": json.dumps([["Tender Opportunity", "workflow_state", "=", "Won"]])
    }).insert(ignore_permissions=True)
    print("✔ Created Chart: Win Volume by Sector")

    # ==============================================================================
    # 3. UPDATE WORKSPACE LAYOUT
    # ==============================================================================
    ws_name = "Tender Management"
    
    # Define the new "Strategic" Layout
    ws_content = [
        {"type": "header", "data": {"text": "Strategic Overview", "level": 2}},
        
        # Row 1: KPI Cards
        {"type": "card", "data": {"card_name": "Tender Win Rate", "col": 4}},
        {"type": "card", "data": {"card_name": "Total Pipeline Value", "col": 4}},
        {"type": "card", "data": {"card_name": "Bids Due Soon", "col": 4}},

        {"type": "header", "data": {"text": "Performance Analysis", "level": 2}},
        
        # Row 2: Charts
        {"type": "chart", "data": {"chart_name": "Strategic Bid Funnel", "col": 8}},
        {"type": "chart", "data": {"chart_name": "Win Volume by Sector", "col": 4}},

        {"type": "header", "data": {"text": "Execution Links", "level": 2}},
        
        # Row 3: Shortcuts
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "label": "Tender Registry", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Tender Content Library", "label": "Knowledge Base", "icon": "book", "color": "Teal"}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "label": "Bond Tracking", "icon": "lock", "color": "Orange"}}
    ]

    if frappe.db.exists("Workspace", ws_name):
        frappe.delete_doc("Workspace", ws_name, force=True)

    # Clean up user views
    frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name = %s", (ws_name,))
    
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
    print("--- ✅ DASHBOARD UPGRADED TO STRATEGIC MODEL ---")

if __name__ == "__main__":
    run()

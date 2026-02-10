import frappe
import json

def run():
    print("--- 🆕 CREATING FRESH WORKSPACE 'TENDER STRATEGY' ---")

    # 1. DESTROY THE OLD WORKSPACE (Scorched Earth)
    old_ws = "Tender Management"
    frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name = %s", (old_ws,))
    frappe.db.sql("DELETE FROM `tabWorkspace` WHERE label = %s", (old_ws,))
    print("✔ Deleted broken 'Tender Management' workspace.")

    # 2. CREATE FRESH ASSETS (New IDs to avoid cache conflicts)
    
    # Card 1: Wins
    if not frappe.db.exists("Number Card", "KPI Wins"):
        frappe.get_doc({
            "doctype": "Number Card",
            "name": "KPI Wins",
            "label": "Total Wins",
            "function": "Count",
            "document_type": "Tender Opportunity",
            "filters_json": json.dumps([["Tender Opportunity", "workflow_state", "=", "Won"]]),
            "color": "#2ecc71"
        }).insert(ignore_permissions=True)

    # Card 2: Pipeline
    if not frappe.db.exists("Number Card", "KPI Pipeline"):
        frappe.get_doc({
            "doctype": "Number Card",
            "name": "KPI Pipeline",
            "label": "Pipeline Value",
            "function": "Sum",
            "aggregate_function_based_on": "final_bid_price",
            "document_type": "Tender Opportunity",
            "filters_json": json.dumps([["Tender Opportunity", "workflow_state", "in", ["Submitted", "Approved to Bid"]]]),
            "color": "#3498db"
        }).insert(ignore_permissions=True)

    # Chart 1: Funnel
    if not frappe.db.exists("Dashboard Chart", "Chart Funnel"):
        frappe.get_doc({
            "doctype": "Dashboard Chart",
            "chart_name": "Chart Funnel",
            "chart_type": "Group By",
            "document_type": "Tender Opportunity",
            "group_by_based_on": "workflow_state", 
            "type": "Bar",
            "is_public": 1,
            "color": "#9b59b6",
            "filters_json": json.dumps([["Tender Opportunity", "workflow_state", "!=", "Draft"]])
        }).insert(ignore_permissions=True)

    # 3. CREATE THE NEW WORKSPACE
    new_ws_name = "Tender Strategy"
    
    ws_content = [
        {"type": "header", "data": {"text": "Tender Performance", "level": 2}},
        {"type": "card", "data": {"card_name": "KPI Wins", "col": 6}},
        {"type": "card", "data": {"card_name": "KPI Pipeline", "col": 6}},
        
        {"type": "header", "data": {"text": "Analysis", "level": 2}},
        {"type": "chart", "data": {"chart_name": "Chart Funnel", "col": 12}},
        
        {"type": "header", "data": {"text": "Quick Links", "level": 2}},
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "type": "DocType", "label": "Tender Registry", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Tender Content Library", "type": "DocType", "label": "Content Library", "icon": "book", "color": "Teal"}}
    ]

    if frappe.db.exists("Workspace", new_ws_name):
        frappe.delete_doc("Workspace", new_ws_name, force=True)

    doc = frappe.get_doc({
        "doctype": "Workspace",
        "name": new_ws_name,
        "label": "Tender Dashboard", # Display Name
        "title": "Tender Dashboard",
        "module": "Tender Management",
        "public": 1,
        "is_standard": 0,
        "content": json.dumps(ws_content)
    })
    doc.insert(ignore_permissions=True)

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ NEW WORKSPACE 'Tender Strategy' CREATED ---")

if __name__ == "__main__":
    run()

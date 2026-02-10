import frappe
import json

def run():
    print("--- 🏗️ SAFE WORKSPACE REBUILD (FIXED) ---")

    ws_name = "Tender Management"

    # 1. DELETE BROKEN WORKSPACE
    frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name = %s", (ws_name,))
    
    # 2. CREATE A SIMPLE TEST CHART (Verified Config)
    # We use a simple "Count" chart which is impossible to break
    chart_name = "Total Tenders Test"
    if frappe.db.exists("Dashboard Chart", chart_name):
        frappe.delete_doc("Dashboard Chart", chart_name, force=True)

    frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": chart_name,
        "chart_type": "Group By",  # Changed to Group By for safety
        "group_by_based_on": "workflow_state", # Simple grouping
        "document_type": "Tender Opportunity",
        "type": "Bar",
        "timeseries": 0, # EXPLICITLY DISABLE TIMESERIES
        "is_public": 1,
        "color": "#3498db"
    }).insert(ignore_permissions=True)
    print("✔ Created Safe Test Chart")

    # 3. BUILD SAFE WORKSPACE
    # Only Shortcuts + 1 Simple Chart
    ws_content = [
        {"type": "header", "data": {"text": "Tender Console", "level": 2}},
        
        # The Safe Chart
        {"type": "chart", "data": {"chart_name": chart_name, "col": 12}},

        {"type": "header", "data": {"text": "Lists", "level": 2}},
        
        # The Shortcuts (We know these work)
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "type": "DocType", "label": "Tender Registry", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Tender Bid", "type": "DocType", "label": "Bids", "icon": "users", "color": "Purple"}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "type": "DocType", "label": "Bid Bonds", "icon": "lock", "color": "Orange"}}
    ]

    doc = frappe.get_doc({
        "doctype": "Workspace",
        "name": ws_name,
        "label": "Tender Management",
        "title": "Tender Management",
        "module": "Tender Management",
        "public": 1,
        "is_standard": 0,
        "content": json.dumps(ws_content)
    })
    doc.insert(ignore_permissions=True)
    print("✔ Rebuilt Workspace (Safe Mode)")

    # 4. RE-ENABLE CLIENT SCRIPTS
    frappe.db.sql("UPDATE `tabClient Script` SET enabled=1 WHERE module='Tender Management'")
    print("✔ Re-enabled Client Logic")

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ REBUILD COMPLETE ---")

if __name__ == "__main__":
    run()

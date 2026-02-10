import frappe
from frappe.utils import add_days, nowdate
import json
import random

def run():
    print("--- 🔧 FIXING DASHBOARD FIELD MISMATCH ---")

    # 1. ENSURE CORRECT FIELDS EXIST
    # We make sure 'submission_deadline' is the actual field name
    if not frappe.db.has_column("Tender Opportunity", "submission_deadline"):
        print("⚠️ Column 'submission_deadline' missing. Adding it...")
        from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
        create_custom_fields({
            "Tender Opportunity": [
                {"fieldname": "submission_deadline", "label": "Submission Deadline", "fieldtype": "Date", "insert_after": "sector"},
                {"fieldname": "final_bid_price", "label": "Final Bid Price", "fieldtype": "Currency", "read_only": 1, "insert_after": "workflow_state"}
            ]
        })
        frappe.db.commit()

    # 2. GENERATE COMPATIBLE SAMPLE DATA
    # We clear old data to prevent "Duplicate" errors and confusion
    frappe.db.sql("DELETE FROM `tabTender Opportunity` WHERE title LIKE '%(Sample)'")

    tenders = [
        {"title": "HQ Office (Sample)", "state": "Submitted", "price": 15000000, "date": 2},
        {"title": "Generator Supply (Sample)", "state": "Won", "price": 4500000, "date": -10},
        {"title": "Rural Road (Sample)", "state": "Lost", "price": 22000000, "date": -25},
        {"title": "HVAC Install (Sample)", "state": "Draft", "price": 850000, "date": 5}
    ]

    print("... Re-populating Data")
    for t in tenders:
        doc = frappe.get_doc({
            "doctype": "Tender Opportunity",
            "tender_number": f"S-{random.randint(100,999)}",
            "title": t["title"],
            "workflow_state": "Draft", # Start at Draft
            "final_bid_price": t["price"],
            "bond_type": "CPO",
            "bond_amount": 10000,
            "submission_deadline": add_days(nowdate(), t["date"]) # CORRECT FIELD NAME
        })
        doc.insert(ignore_permissions=True, ignore_mandatory=True)
        
        # Force Status
        frappe.db.set_value("Tender Opportunity", doc.name, "workflow_state", t["state"])
        print(f"✔ Created: {t['title']}")

    # 3. REBUILD CHARTS (With Correct Field Names)
    charts = [
        {
            "name": "SOP Pipeline Value",
            "type": "Bar",
            "y_axis": "final_bid_price",
            "group_by": "workflow_state"
        },
        {
            "name": "SOP Win Ratio",
            "type": "Donut",
            "y_axis": None, # Count doesn't need Y-axis
            "group_by": "workflow_state"
        }
    ]

    for c in charts:
        if frappe.db.exists("Dashboard Chart", c["name"]):
            frappe.delete_doc("Dashboard Chart", c["name"])
        
        new_chart = frappe.get_doc({
            "doctype": "Dashboard Chart",
            "chart_name": c["name"],
            "chart_type": "Group By" if c["type"] == "Bar" else "Count",
            "document_type": "Tender Opportunity",
            "group_by_based_on": c["group_by"],
            "aggregate_function_based_on": c["y_axis"],
            "aggregate_function": "Sum" if c["type"] == "Bar" else None,
            "based_on": "creation", # Fallback for Count
            "type": c["type"],
            "timeseries": 0,
            "is_public": 1,
            "filters_json": "[]"
        })
        new_chart.insert(ignore_permissions=True)
        print(f"✔ Chart Fixed: {c['name']}")

    # 4. REBUILD WORKSPACE (With Correct Shortcut Filter)
    ws_name = "Tender Management"
    if frappe.db.exists("Workspace", ws_name):
        frappe.delete_doc("Workspace", ws_name, force=True)

    # Clean user personalizations again
    frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name=%s AND public=0", (ws_name,))

    ws_content = [
        {"type": "header", "data": {"text": "Tender Performance", "level": 2}},
        {"type": "chart", "data": {"chart_name": "SOP Pipeline Value", "col": 12}},
        {"type": "chart", "data": {"chart_name": "SOP Win Ratio", "col": 12}},
        {"type": "header", "data": {"text": "Quick Links", "level": 2}},
        {
            "type": "shortcut", 
            "data": {
                "link_to": "Tender Opportunity", 
                "label": "Deadlines This Week", 
                "icon": "calendar", 
                "color": "Red",
                # CRITICAL FIX: Filter MUST match the actual field name 'submission_deadline'
                "stats_filter": json.dumps({"submission_deadline": ["Timespan", "This Week"]})
            }
        },
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "label": "All Tenders", "icon": "list", "color": "Blue"}}
    ]

    ws = frappe.get_doc({
        "doctype": "Workspace",
        "name": ws_name,
        "label": ws_name,
        "title": ws_name,
        "module": "Tender Management",
        "public": 1,
        "content": json.dumps(ws_content)
    })
    ws.insert(ignore_permissions=True)

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ REPAIR COMPLETE ---")

if __name__ == "__main__":
    run()

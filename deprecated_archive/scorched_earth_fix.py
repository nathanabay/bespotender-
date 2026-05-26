import frappe
import json
from frappe.utils import add_days, nowdate
import random

def run():
    print("--- ☢️ INITIATING SCORCHED EARTH WORKSPACE RESET ---")

    ws_name = "Tender Management"

    # 1. NUCLEAR WIPE OF WORKSPACES
    # Delete ALL workspaces with this name, regardless of owner, public/private, or standard status.
    # This ensures no "ghost" empty views remain.
    frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name = %s", (ws_name,))
    frappe.db.sql("DELETE FROM `tabWorkspace` WHERE label = %s", (ws_name,))
    print(f"✔ DELETE: All versions of Workspace '{ws_name}' destroyed.")

    # 2. RECREATE THE MASTER WORKSPACE
    # We create a fresh, clean Public workspace.
    ws_content = [
        {"type": "header", "data": {"text": "Tender Performance", "level": 2}},
        {"type": "chart", "data": {"chart_name": "SOP Pipeline Value", "col": 12}},
        {"type": "chart", "data": {"chart_name": "SOP Win Ratio", "col": 6}},
        {"type": "header", "data": {"text": "Quick Links", "level": 2}},
        {
            "type": "shortcut", 
            "data": {
                "link_to": "Tender Opportunity", 
                "label": "Deadlines This Week", 
                "icon": "calendar", 
                "color": "Red",
                "stats_filter": json.dumps({"submission_deadline": ["Timespan", "This Week"]})
            }
        },
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "label": "Tender Registry", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "label": "Bid Bonds", "icon": "lock", "color": "Orange"}}
    ]

    doc = frappe.get_doc({
        "doctype": "Workspace",
        "name": ws_name,
        "label": ws_name,
        "title": ws_name,
        "module": "Tender Management",
        "category": "Modules",
        "public": 1, 
        "is_standard": 0,
        "content": json.dumps(ws_content)
    })
    doc.insert(ignore_permissions=True)
    print(f"✔ CREATE: New Public Workspace '{ws_name}' created.")

    # 3. ENSURE CHARTS ARE PUBLIC
    # If charts exist but are private, they won't show up.
    charts = ["SOP Pipeline Value", "SOP Win Ratio"]
    for c in charts:
        if frappe.db.exists("Dashboard Chart", c):
            frappe.db.set_value("Dashboard Chart", c, "is_public", 1)
            print(f"✔ FIX: Chart '{c}' set to Public.")

    # 4. RE-VERIFY DATA (Just to be safe)
    if not frappe.db.count("Tender Opportunity"):
        print("⚠️ No data found! Generating sample data...")
        # Create one sample just so charts aren't empty
        sample = frappe.get_doc({
            "doctype": "Tender Opportunity",
            "title": "Sample HQ Construction",
            "tender_number": "SMPL-001",
            "workflow_state": "Submitted",
            "final_bid_price": 5000000,
            "submission_deadline": add_days(nowdate(), 2)
        })
        sample.insert(ignore_permissions=True, ignore_mandatory=True)
        print("✔ DATA: Sample Record Created.")

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ RESET COMPLETE: YOU MUST RELOAD YOUR BROWSER ---")

if __name__ == "__main__":
    run()

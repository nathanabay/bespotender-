import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import add_days, nowdate
import json
import random

def run():
    print("--- 🚀 STARTING MASTER REPAIR SEQUENCE ---")

    # ==============================================================================
    # 1. FIX DOCTYPE & FIELDS (The Root Cause of "Status" Errors)
    # ==============================================================================
    print("... Repairing DocType Fields")
    
    # A. Force-Update Status Options
    sop_states = "Draft\nUnder Evaluation\nApproved to Bid\nTender Purchased\nBid Bond Issued\nTechnical Preparation\nFinancial Preparation\nReady for Submission\nSubmitted\nUnder Client Evaluation\nWon\nLost"
    
    try:
        doc = frappe.get_doc("DocType", "Tender Opportunity")
        for field in doc.fields:
            if field.fieldname == "workflow_state":
                field.options = sop_states
                break
        doc.save(ignore_permissions=True)
        print("✔ 'workflow_state' options updated.")
    except Exception as e:
        print(f"⚠️ DocType update skipped: {e}")

    # B. Ensure Deadline Field Exists
    fields = {
        "Tender Opportunity": [
            {"fieldname": "submission_deadline", "label": "Submission Deadline", "fieldtype": "Datetime", "insert_after": "sector"},
            {"fieldname": "final_bid_price", "label": "Final Bid Price", "fieldtype": "Currency", "read_only": 1, "insert_after": "workflow_state"}
        ]
    }
    create_custom_fields(fields)
    
    frappe.db.commit() # Save schema changes immediately

    # ==============================================================================
    # 2. GENERATE SAMPLE DATA (To Fix "Blank/No Data" Charts)
    # ==============================================================================
    print("... Generating Sample Data")
    
    # Clear old junk data
    frappe.db.sql("DELETE FROM `tabTender Opportunity` WHERE title LIKE '%(Sample)'")
    
    samples = [
        {"title": "HQ Construction (Sample)", "sector": "Construction", "state": "Submitted", "price": 15000000, "days": 2},
        {"title": "Generator Supply (Sample)", "sector": "Electro-Mechanical", "state": "Won", "price": 4500000, "days": -10},
        {"title": "Rural Road (Sample)", "sector": "Construction", "state": "Lost", "price": 22000000, "days": -25},
        {"title": "HVAC Install (Sample)", "sector": "Electro-Mechanical", "state": "Draft", "price": 850000, "days": 5},
        {"title": "Water Works (Sample)", "sector": "General Supply", "state": "Approved to Bid", "price": 3000000, "days": 10},
    ]

    for s in samples:
        doc = frappe.get_doc({
            "doctype": "Tender Opportunity",
            "title": s["title"],
            "tender_number": f"SMPL-{random.randint(100,999)}",
            "sector": s["sector"],
            "workflow_state": s["state"], # Now valid!
            "final_bid_price": s["price"],
            "submission_deadline": add_days(nowdate(), s["days"])
        })
        # Use ignore_validate to bypass any strict workflow rules during setup
        doc.insert(ignore_permissions=True, ignore_mandatory=True)
        print(f"✔ Created: {s['title']}")

    # ==============================================================================
    # 3. REBUILD DASHBOARD (Without 'is_standard' column)
    # ==============================================================================
    print("... Rebuilding Dashboard")
    
    ws_name = "Tender Management"
    
    # A. Delete old workspace & charts
    frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name=%s", (ws_name,))
    for c in ["SOP Pipeline", "SOP Win Ratio"]:
        frappe.db.sql("DELETE FROM `tabDashboard Chart` WHERE name=%s", (c,))

    # B. Create Charts (Public)
    # Chart 1: Pipeline
    c1 = frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": "SOP Pipeline",
        "chart_type": "Group By",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "workflow_state",
        "aggregate_function_based_on": "final_bid_price",
        "aggregate_function": "Sum",
        "type": "Bar",
        "timeseries": 0,
        "is_public": 1,
        "filters_json": "[]"
    })
    c1.insert(ignore_permissions=True)

    # Chart 2: Win Ratio
    c2 = frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": "SOP Win Ratio",
        "chart_type": "Count",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "workflow_state",
        "based_on": "creation",
        "timeseries": 0,
        "is_public": 1,
        "type": "Donut",
        "filters_json": json.dumps([["Tender Opportunity", "workflow_state", "in", ["Won", "Lost"]]])
    })
    c2.insert(ignore_permissions=True)

    # C. Create Workspace (Public)
    ws_content = [
        {"type": "header", "data": {"text": "Performance Overview", "level": 2}},
        {"type": "chart", "data": {"chart_name": "SOP Pipeline", "col": 12}},
        {"type": "chart", "data": {"chart_name": "SOP Win Ratio", "col": 6}},
        {"type": "header", "data": {"text": "Quick Links", "level": 2}},
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "label": "Tender Registry", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "label": "Bid Bonds", "icon": "lock", "color": "Orange"}}
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
    print("--- ✅ SUCCESS: DASHBOARD IS LIVE ---")

if __name__ == "__main__":
    run()

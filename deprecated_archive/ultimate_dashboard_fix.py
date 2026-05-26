import frappe
from frappe.utils import add_days, nowdate
import json
import random

def run():
    print("--- ☢️ STARTING NUCLEAR DASHBOARD RESET ---")

    # ==============================================================================
    # 1. CLEANUP (Delete old broken files)
    # ==============================================================================
    ws_name = "Tender Management"
    
    # Force delete existing workspace to clear "blank" cache
    if frappe.db.exists("Workspace", ws_name):
        frappe.delete_doc("Workspace", ws_name, force=True)
        print(f"✔ Cleared old Workspace: {ws_name}")

    # Delete existing charts to prevent conflicts
    charts = ["SOP Total Bid Value", "SOP Win Ratio", "SOP Bond Exposure"]
    for c in charts:
        if frappe.db.exists("Dashboard Chart", c):
            frappe.delete_doc("Dashboard Chart", c, force=True)
            print(f"✔ Cleared old Chart: {c}")

    # ==============================================================================
    # 2. CREATE CHARTS (With correct 'Group By' settings)
    # ==============================================================================
    
    # Chart 1: Pipeline Value (Bar)
    c1 = frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": "SOP Total Bid Value",
        "chart_type": "Group By",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "workflow_state",
        "aggregate_function_based_on": "final_bid_price",
        "aggregate_function": "Sum",
        "type": "Bar",
        "timeseries": 0, # Critical: Disable time series
        "is_public": 1,
        "filters_json": "[]"
    })
    c1.insert(ignore_permissions=True)
    print("✔ Recreated Chart: Pipeline Value")

    # Chart 2: Win Ratio (Donut)
    c2 = frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": "SOP Win Ratio",
        "chart_type": "Count",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "workflow_state",
        "based_on": "creation", # Count needs a field to count
        "timeseries": 0,
        "is_public": 1,
        "filters_json": json.dumps([["Tender Opportunity", "workflow_state", "in", ["Won", "Lost"]]]),
        "type": "Donut"
    })
    c2.insert(ignore_permissions=True)
    print("✔ Recreated Chart: Win Ratio")

    # Chart 3: Bond Exposure (Percentage)
    c3 = frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": "SOP Bond Exposure",
        "chart_type": "Group By",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "bond_type",
        "aggregate_function_based_on": "bond_amount",
        "aggregate_function": "Sum",
        "type": "Percentage",
        "timeseries": 0,
        "is_public": 1,
        "filters_json": "[]"
    })
    c3.insert(ignore_permissions=True)
    print("✔ Recreated Chart: Bond Exposure")

    # ==============================================================================
    # 3. GENERATE SAMPLE DATA (To prevent empty charts)
    # ==============================================================================
    
    # Ensure field options are correct first
    sop_states_list = "Draft\nUnder Evaluation\nApproved to Bid\nTender Purchased\nBid Bond Issued\nTechnical Preparation\nFinancial Preparation\nReady for Submission\nSubmitted\nUnder Client Evaluation\nWon\nLost"
    
    doc_meta = frappe.get_doc("DocType", "Tender Opportunity")
    for f in doc_meta.fields:
        if f.fieldname == "workflow_state":
            f.options = sop_states_list
            break
    doc_meta.save(ignore_permissions=True)
    
    tenders = [
        {"title": "Construction of HQ (Sample)", "sector": "Construction", "state": "Submitted", "price": 5000000, "bond": "CPO", "b_amt": 50000},
        {"title": "500kVA Generator (Sample)", "sector": "Electro-Mechanical", "state": "Won", "price": 2500000, "bond": "Bank Guarantee", "b_amt": 25000},
        {"title": "Road Renovation (Sample)", "sector": "Construction", "state": "Lost", "price": 8000000, "bond": "Insurance Bond", "b_amt": 80000},
        {"title": "HVAC Install (Sample)", "sector": "Electro-Mechanical", "state": "Technical Preparation", "price": 1200000, "bond": "CPO", "b_amt": 12000}
    ]

    for t in tenders:
        if not frappe.db.exists("Tender Opportunity", {"title": t["title"]}):
            new_doc = frappe.get_doc({
                "doctype": "Tender Opportunity",
                "tender_number": f"T-{random.randint(1000,9999)}",
                "title": t["title"],
                "sector": t["sector"],
                "workflow_state": "Draft", # Start Draft
                "final_bid_price": t["price"],
                "bond_type": t["bond"],
                "bond_amount": t["b_amt"],
                "deadline": add_days(nowdate(), 5)
            })
            new_doc.insert(ignore_permissions=True)
            # Force update to final state to bypass workflow rules for setup
            frappe.db.set_value("Tender Opportunity", new_doc.name, "workflow_state", t["state"])
            print(f"✔ Data Created: {t['title']}")

    # ==============================================================================
    # 4. BUILD THE WORKSPACE
    # ==============================================================================
    ws_content = [
        {"type": "header", "data": {"text": "Tender Performance (SOP)", "level": 2}},
        {"type": "chart", "data": {"chart_name": "SOP Total Bid Value", "col": 12}},
        {"type": "chart", "data": {"chart_name": "SOP Win Ratio", "col": 6}},
        {"type": "chart", "data": {"chart_name": "SOP Bond Exposure", "col": 6}},
        {"type": "header", "data": {"text": "Operational Links", "level": 2}},
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "label": "All Tenders", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "label": "Bid Bonds", "icon": "lock", "color": "Orange"}},
        {"type": "shortcut", "data": {"link_to": "Payment Entry", "label": "Tender Fees", "icon": "credit-card", "color": "Green"}}
    ]

    ws = frappe.get_doc({
        "doctype": "Workspace",
        "name": ws_name,
        "label": ws_name,
        "title": ws_name,
        "category": "Modules",
        "module": "Tender Management",
        "public": 1,
        "is_standard": 0,
        "content": json.dumps(ws_content)
    })
    ws.insert(ignore_permissions=True)
    print(f"✔ Workspace '{ws_name}' Rebuilt Successfully")

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ SUCCESS! DASHBOARD IS LIVE ---")

if __name__ == "__main__":
    run()

import frappe
from frappe.utils import add_days, nowdate
import json
import random

def run():
    print("--- 🔧 FIXING FIELD OPTIONS & POPULATING DATA ---")

    # 1. UPDATE FIELD OPTIONS (Critical Fix)
    # The system is rejecting "Draft" because the field options are stale.
    sop_states_list = [
        "Draft", "Under Evaluation", "Approved to Bid", 
        "Tender Purchased", "Bid Bond Issued", "Technical Preparation", 
        "Financial Preparation", "Ready for Submission", "Submitted", 
        "Under Client Evaluation", "Won", "Lost"
    ]
    
    if frappe.db.exists("DocType", "Tender Opportunity"):
        doc = frappe.get_doc("DocType", "Tender Opportunity")
        for field in doc.fields:
            if field.fieldname == "workflow_state":
                field.options = "\n".join(sop_states_list)
                print("✔ Updated 'workflow_state' options to match SOP")
                break
        doc.save(ignore_permissions=True)

    # 2. ENSURE WORKFLOW IS LINKED
    wf_name = "Tender Register Workflow"
    if frappe.db.exists("Workflow", wf_name):
        wf = frappe.get_doc("Workflow", wf_name)
        if not wf.is_active:
            wf.is_active = 1
            wf.save(ignore_permissions=True)
            print("✔ Workflow 'Tender Register Workflow' set to Active")

    frappe.db.commit()

    # 3. GENERATE SAMPLE DATA
    tenders = [
        {
            "title": "Construction of HQ Office (Sample)",
            "sector": "Construction",
            "target_state": "Submitted",
            "final_bid_price": 5000000,
            "bond_type": "CPO",
            "bond_amount": 50000,
            "bond_status": "Active",
            "deadline": add_days(nowdate(), 2) 
        },
        {
            "title": "Supply of 500kVA Generator (Sample)",
            "sector": "Electro-Mechanical",
            "target_state": "Won",
            "final_bid_price": 2500000,
            "bond_type": "Bank Guarantee",
            "bond_amount": 25000,
            "bond_status": "Active",
            "deadline": add_days(nowdate(), -10)
        },
        {
            "title": "Road Renovation Project (Sample)",
            "sector": "Construction",
            "target_state": "Lost",
            "final_bid_price": 8000000,
            "bond_type": "Insurance Bond",
            "bond_amount": 80000,
            "bond_status": "Released",
            "deadline": add_days(nowdate(), -20)
        },
        {
            "title": "HVAC Installation (Sample)",
            "sector": "Electro-Mechanical",
            "target_state": "Technical Preparation",
            "final_bid_price": 1200000,
            "bond_type": "CPO",
            "bond_amount": 12000,
            "bond_status": "Pending",
            "deadline": add_days(nowdate(), 5)
        }
    ]

    print("... Creating Sample Records")
    for t in tenders:
        # Check if exists to avoid duplicates
        if not frappe.db.exists("Tender Opportunity", {"title": t["title"]}):
            # Step A: Insert as Draft
            new_doc = frappe.get_doc({
                "doctype": "Tender Opportunity",
                "tender_number": f"T-2026-{random.randint(100,999)}",
                "title": t["title"],
                "sector": t["sector"],
                "workflow_state": "Draft", 
                "final_bid_price": t["final_bid_price"],
                "bond_type": t["bond_type"],
                "bond_amount": t["bond_amount"],
                "bond_status": t["bond_status"],
                "deadline": t["deadline"]
            })
            new_doc.insert(ignore_permissions=True)
            
            # Step B: Force Update to Target State
            frappe.db.set_value("Tender Opportunity", new_doc.name, "workflow_state", t["target_state"])
            print(f"✔ Created: {t['title']}")

    # 4. DASHBOARD FINALIZATION (SOP Sec 5)
    ws_name = "Tender Management"
    # Content structure
    ws_content = [
        {"type": "header", "data": {"text": "Tender Performance (SOP)", "level": 2}},
        {"type": "chart", "data": {"chart_name": "SOP Total Bid Value", "col": 12}},
        {"type": "chart", "data": {"chart_name": "SOP Win Ratio", "col": 6}},
        {"type": "chart", "data": {"chart_name": "SOP Bond Exposure", "col": 6}},
        {"type": "header", "data": {"text": "Action Required", "level": 2}},
        {
            "type": "shortcut", 
            "data": {
                "link_to": "Tender Opportunity", 
                "label": "Deadlines This Week", 
                "icon": "calendar", 
                "color": "Red",
                "stats_filter": json.dumps({"deadline": ["Timespan", "This Week"]})
            }
        },
        {"type": "header", "data": {"text": "Operational Links", "level": 2}},
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "label": "All Tenders", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "label": "Bid Bonds", "icon": "lock", "color": "Orange"}}
    ]

    # Force Update Workspace
    if frappe.db.exists("Workspace", ws_name):
        w = frappe.get_doc("Workspace", ws_name)
        w.content = json.dumps(ws_content)
        w.public = 1
        w.save(ignore_permissions=True)
        print("✔ Workspace Dashboard Updated")

    frappe.db.commit()
    print("--- ✅ REPAIR COMPLETE: RELOAD BROWSER ---")

if __name__ == "__main__":
    run()

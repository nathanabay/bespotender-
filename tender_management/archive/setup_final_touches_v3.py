import frappe
from frappe.utils import add_days, nowdate
import json
import random

def run():
    print("--- 🚀 POPULATING DATA & FINALIZING DASHBOARD (V3) ---")

    # 1. GENERATE SAMPLE TENDERS (Insert as Draft -> Force Update)
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
        if not frappe.db.exists("Tender Opportunity", {"title": t["title"]}):
            # Step A: Insert as Draft (Safe default)
            doc = frappe.get_doc({
                "doctype": "Tender Opportunity",
                "tender_number": f"T-2026-{random.randint(100,999)}",
                "title": t["title"],
                "sector": t["sector"],
                "workflow_state": "Draft", # Start at Draft to pass validation
                "final_bid_price": t["final_bid_price"],
                "bond_type": t["bond_type"],
                "bond_amount": t["bond_amount"],
                "bond_status": t["bond_status"],
                "deadline": t["deadline"]
            })
            doc.insert(ignore_permissions=True)
            
            # Step B: Force Update to Target State (Bypass Workflow)
            frappe.db.set_value("Tender Opportunity", doc.name, "workflow_state", t["target_state"])
            print(f"✔ Created & Updated: {t['title']} -> {t['target_state']}")

    # 2. UPDATE WORKSPACE WITH 'DEADLINES' SHORTCUT (SOP Sec 5)
    ws_name = "Tender Management"
    if frappe.db.exists("Workspace", ws_name):
        doc = frappe.get_doc("Workspace", ws_name)
        
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
        
        doc.content = json.dumps(ws_content)
        doc.save(ignore_permissions=True)
        print("✔ Workspace Updated")

    frappe.db.commit()
    print("--- ✅ SUCCESS: DATA GENERATED & DASHBOARD FINALIZED ---")

if __name__ == "__main__":
    run()

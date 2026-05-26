import frappe
from frappe.utils import add_days, nowdate
import random

def run():
    print("--- 📊 INJECTING DUMMY DATA (FORCE MODE) ---")

    scenarios = [
        {"title": "Headquarters Security System", "sector": "Electro-Mechanical", "state": "Won", "price": 5000000},
        {"title": "Rural Road Maintenance Phase 1", "sector": "Construction", "state": "Lost", "price": 12000000},
        {"title": "City Water Pump Upgrade", "sector": "Water Works", "state": "Submitted", "price": 8500000},
        {"title": "Generator Annual Maintenance", "sector": "Maintenance", "state": "Draft", "price": 400000},
        {"title": "Hospital HVAC Installation", "sector": "Electro-Mechanical", "state": "Won", "price": 15000000},
        {"title": "School Building Block B", "sector": "Construction", "state": "Submitted", "price": 22000000},
        {"title": "Fiber Optic Cabling", "sector": "General Supply", "state": "Lost", "price": 3000000},
        {"title": "Solar Panel Supply", "sector": "General Supply", "state": "Won", "price": 6000000},
        {"title": "Waste Water Treatment Plant", "sector": "Water Works", "state": "Submitted", "price": 45000000},
        {"title": "Office Complex Wiring", "sector": "Electro-Mechanical", "state": "Draft", "price": 1200000}
    ]

    count = 0
    for s in scenarios:
        if not frappe.db.exists("Tender Opportunity", {"title": s["title"]}):
            doc = frappe.get_doc({
                "doctype": "Tender Opportunity",
                "title": s["title"],
                "sector": s["sector"],
                "tender_number": f"TEST-{random.randint(1000, 9999)}",
                "status": "Closed" if s["state"] in ["Won", "Lost"] else "Open",
                "workflow_state": s["state"], # This is what we want
                "submission_deadline": add_days(nowdate(), random.randint(-30, 30)),
                "final_bid_price": s["price"],
                "estimated_cost": s["price"] * 0.8
            })
            
            # THE FIX: Bypassing workflow validation
            doc.flags.ignore_permissions = True
            doc.flags.ignore_validate = True 
            doc.flags.ignore_workflow = True # Magic flag
            doc.insert()
            
            # Double Tap: Ensure state is stuck
            frappe.db.set_value("Tender Opportunity", doc.name, "workflow_state", s["state"])
            
            print(f"✔ Created: {s['title']} ({s['state']})")
            count += 1
        else:
            print(f"   Skipped (Exists): {s['title']}")

    frappe.db.commit()
    print(f"--- ✅ ADDED {count} NEW RECORDS ---")

if __name__ == "__main__":
    run()

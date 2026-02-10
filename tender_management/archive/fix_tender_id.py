import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import add_days, nowdate
import json
import random

def run():
    print("--- 🆔 UPDATING TENDER ID FORMAT ---")

    # 1. MODIFY DOCTYPE CONFIGURATION
    if frappe.db.exists("DocType", "Tender Opportunity"):
        doc = frappe.get_doc("DocType", "Tender Opportunity")
        
        # Ensure 'title' field exists
        has_title = False
        for field in doc.fields:
            if field.fieldname == 'title':
                has_title = True
                break
        
        if not has_title:
            # Create title field if missing
            doc.append("fields", {
                "fieldname": "title",
                "label": "Tender Name",
                "fieldtype": "Data",
                "reqd": 1,
                "in_list_view": 1,
                "insert_after": "naming_series"
            })

        # CRITICAL CHANGE: Set ID to come from the 'title' field
        doc.autoname = "field:title"
        doc.title_field = "title"
        
        doc.save(ignore_permissions=True)
        print("✔ DocType Updated: ID = Tender Name")

    # 2. FLUSH OLD DATA
    # We must wipe old records because their IDs (e.g. T-2026-001) are now invalid formats
    frappe.db.sql("DELETE FROM `tabTender Opportunity`")
    print("✔ Cleared old records.")

    # 3. REGENERATE DATA WITH NEW IDS
    tenders = [
        {"title": "HQ Office Construction", "sector": "Construction", "state": "Submitted", "price": 15000000, "days": 2},
        {"title": "Generator Supply 500kVA", "sector": "Electro-Mechanical", "state": "Won", "price": 4500000, "days": -10},
        {"title": "Rural Road Project", "sector": "Construction", "state": "Lost", "price": 22000000, "days": -25},
        {"title": "HVAC Maintenance Contract", "sector": "Electro-Mechanical", "state": "Draft", "price": 850000, "days": 5},
        {"title": "Water Works Phase 2", "sector": "General Supply", "state": "Approved to Bid", "price": 3000000, "days": 10},
    ]

    print("... Creating New Records")
    for t in tenders:
        doc = frappe.get_doc({
            "doctype": "Tender Opportunity",
            "title": t["title"], # This becomes the ID
            "tender_number": f"REF-{random.randint(100,999)}",
            "sector": t["sector"],
            "workflow_state": "Draft", 
            "final_bid_price": t["price"],
            "bond_type": "CPO",
            "bond_amount": 10000,
            "submission_deadline": add_days(nowdate(), t["days"])
        })
        doc.insert(ignore_permissions=True, ignore_mandatory=True)
        
        # Force Status
        frappe.db.set_value("Tender Opportunity", doc.name, "workflow_state", t["state"])
        print(f"✔ Created: {doc.name}") 

    frappe.db.commit()
    print("--- ✅ ID FIX COMPLETE ---")

if __name__ == "__main__":
    run()

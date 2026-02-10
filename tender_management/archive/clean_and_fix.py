import frappe
from frappe.utils import add_days, nowdate
import json
import random

def run():
    print("--- 🛠 REPAIRING DUPLICATE FIELDS & SYSTEM ---")

    # 1. FIX DOCTYPE METADATA (Remove duplicates first)
    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # Filter out existing potentially conflicting fields to start fresh
    new_fields = []
    for f in doc.fields:
        if f.fieldname in ["deadline", "submission_deadline", "naming_series"]:
            continue 
        new_fields.append(f)
        
    doc.fields = new_fields
    
    # Re-add the fields cleanly
    doc.append("fields", {
        "fieldname": "naming_series",
        "label": "Naming Series",
        "fieldtype": "Select",
        "options": "T-CON-.YYYY.-.####\nT-ELEC-.YYYY.-.####\nT-WAT-.YYYY.-.####",
        "hidden": 0,
        "reqd": 1,
        "insert_before": "tender_number"
    })

    doc.append("fields", {
        "fieldname": "submission_deadline",
        "label": "Submission Deadline",
        "fieldtype": "Date",
        "reqd": 1,
        "insert_after": "sector"
    })
    
    # Set Autoname
    doc.autoname = "naming_series:"

    # Update Sector Options
    for f in doc.fields:
        if f.fieldname == "sector":
            f.options = "Construction\nElectro-Mechanical\nMaintenance\nWater Works\nGeneral Supply"

    doc.save(ignore_permissions=True)
    frappe.db.commit()
    print("✔ DocType & Fields Repaired (Duplicates Removed)")

    # 2. CLIENT SCRIPT (Auto-Select ID based on Sector)
    script_name = "Tender Smart ID Logic"
    if frappe.db.exists("Client Script", script_name):
        frappe.delete_doc("Client Script", script_name)

    client_script_content = """
frappe.ui.form.on('Tender Opportunity', {
    sector: function(frm) {
        if (frm.doc.sector == 'Construction') {
            frm.set_value('naming_series', 'T-CON-.YYYY.-.####');
        } else if (frm.doc.sector == 'Electro-Mechanical') {
            frm.set_value('naming_series', 'T-ELEC-.YYYY.-.####');
        } else if (frm.doc.sector == 'Maintenance') {
            frm.set_value('naming_series', 'T-WAT-.YYYY.-.####');
        } else if (frm.doc.sector == 'Water Works') {
            frm.set_value('naming_series', 'T-WAT-.YYYY.-.####');
        } else {
            frm.set_value('naming_series', 'T-CON-.YYYY.-.####');
        }
    }
});
"""
    frappe.get_doc({
        "doctype": "Client Script",
        "dt": "Tender Opportunity",
        "name": script_name,
        "view": "Form",
        "enabled": 1,
        "script": client_script_content
    }).insert(ignore_permissions=True)
    print("✔ Smart ID Automation Installed")

    # 3. GENERATE DATA
    frappe.db.sql("DELETE FROM `tabTender Opportunity`")
    
    tenders = [
        {"title": "HQ Office Construction", "sector": "Construction", "prefix": "T-CON-.YYYY.-.####", "state": "Submitted", "price": 15000000, "days": 2},
        {"title": "Generator Supply 500kVA", "sector": "Electro-Mechanical", "prefix": "T-ELEC-.YYYY.-.####", "state": "Won", "price": 4500000, "days": -10},
        {"title": "Annual Facility Upkeep", "sector": "Maintenance", "prefix": "T-WAT-.YYYY.-.####", "state": "Draft", "price": 850000, "days": 5},
        {"title": "City Water Line Phase 2", "sector": "Water Works", "prefix": "T-WAT-.YYYY.-.####", "state": "Approved to Bid", "price": 3000000, "days": 10},
        {"title": "Rural Road Project", "sector": "Construction", "prefix": "T-CON-.YYYY.-.####", "state": "Lost", "price": 22000000, "days": -20}
    ]

    print("... Creating Data")
    for t in tenders:
        doc = frappe.get_doc({
            "doctype": "Tender Opportunity",
            "title": t["title"],
            "sector": t["sector"],
            "naming_series": t["prefix"],
            "workflow_state": "Draft",
            "final_bid_price": t["price"],
            "submission_deadline": add_days(nowdate(), t["days"])
        })
        doc.insert(ignore_permissions=True)
        
        if t["state"] != "Draft":
            frappe.db.set_value("Tender Opportunity", doc.name, "workflow_state", t["state"])
            
        print(f"✔ Created: {doc.name}")

    frappe.db.commit()
    print("--- ✅ FINAL FIX SUCCESSFUL ---")

if __name__ == "__main__":
    run()

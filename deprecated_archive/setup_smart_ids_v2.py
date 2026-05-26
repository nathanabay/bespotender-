import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import add_days, nowdate
import random

def run():
    print("--- 🆔 CONFIGURING SMART TENDER IDs (FIXED) ---")

    # 1. DEFINE NEW OPTIONS
    new_sectors = "Construction\nElectro-Mechanical\nMaintenance\nWater Works\nGeneral Supply"
    
    # 2. FORCE UPDATE SECTOR OPTIONS
    # Check if it's a Custom Field (most likely) or a Standard Field and update accordingly
    if frappe.db.exists("Custom Field", {"dt": "Tender Opportunity", "fieldname": "sector"}):
        frappe.db.set_value("Custom Field", {"dt": "Tender Opportunity", "fieldname": "sector"}, "options", new_sectors)
        print("✔ Updated 'sector' options via Custom Field")
    else:
        # Fallback: Update DocType directly
        doc = frappe.get_doc("DocType", "Tender Opportunity")
        for field in doc.fields:
            if field.fieldname == "sector":
                field.options = new_sectors
                break
        doc.save(ignore_permissions=True)
        print("✔ Updated 'sector' options via DocType")

    # 3. ENABLE NAMING SERIES
    doc = frappe.get_doc("DocType", "Tender Opportunity")
    doc.autoname = "naming_series:"
    
    # Add naming_series field if missing
    if not any(f.fieldname == 'naming_series' for f in doc.fields):
        doc.append("fields", {
            "fieldname": "naming_series",
            "label": "Naming Series",
            "fieldtype": "Select",
            "options": "T-CON-.YYYY.-\nT-ELEC-.YYYY.-\nT-WAT-.YYYY.-",
            "hidden": 0,
            "reqd": 1,
            "insert_before": "tender_number"
        })
    
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache() # Critical to apply the 'Maintenance' option change
    print("✔ DocType Configured & Cache Cleared")

    # 4. INSTALL CLIENT SCRIPT (Automation)
    script_name = "Tender Smart ID Logic"
    if frappe.db.exists("Client Script", script_name):
        frappe.delete_doc("Client Script", script_name)

    client_script_content = """
frappe.ui.form.on('Tender Opportunity', {
    sector: function(frm) {
        if (frm.doc.sector == 'Construction') {
            frm.set_value('naming_series', 'T-CON-.YYYY.-');
        } else if (frm.doc.sector == 'Electro-Mechanical') {
            frm.set_value('naming_series', 'T-ELEC-.YYYY.-');
        } else if (frm.doc.sector == 'Maintenance') {
            frm.set_value('naming_series', 'T-WAT-.YYYY.-');
        } else if (frm.doc.sector == 'Water Works') {
            frm.set_value('naming_series', 'T-WAT-.YYYY.-');
        } else {
            frm.set_value('naming_series', 'T-GEN-.YYYY.-');
        }
    }
});
"""
    
    cs = frappe.get_doc({
        "doctype": "Client Script",
        "dt": "Tender Opportunity",
        "name": script_name,
        "view": "Form",
        "enabled": 1,
        "script": client_script_content
    })
    cs.insert(ignore_permissions=True)
    print("✔ Client Script Installed")

    # 5. REGENERATE DATA
    frappe.db.sql("DELETE FROM `tabTender Opportunity`")
    
    tenders = [
        {"title": "HQ Office Construction", "sector": "Construction", "prefix": "T-CON-.YYYY.-", "state": "Submitted", "price": 15000000},
        {"title": "Generator Supply 500kVA", "sector": "Electro-Mechanical", "prefix": "T-ELEC-.YYYY.-", "state": "Won", "price": 4500000},
        {"title": "Annual Facility Upkeep", "sector": "Maintenance", "prefix": "T-WAT-.YYYY.-", "state": "Draft", "price": 850000},
        {"title": "City Water Line Expansion", "sector": "Water Works", "prefix": "T-WAT-.YYYY.-", "state": "Approved to Bid", "price": 3000000},
        {"title": "Rural Road Project", "sector": "Construction", "prefix": "T-CON-.YYYY.-", "state": "Lost", "price": 22000000}
    ]

    print("... Creating records with new IDs")
    for t in tenders:
        doc = frappe.get_doc({
            "doctype": "Tender Opportunity",
            "title": t["title"],
            "sector": t["sector"],
            "naming_series": t["prefix"],
            "workflow_state": "Draft",
            "final_bid_price": t["price"],
            "submission_deadline": add_days(nowdate(), 5)
        })
        doc.insert(ignore_permissions=True)
        
        # Force Status
        frappe.db.set_value("Tender Opportunity", doc.name, "workflow_state", t["state"])
        print(f"✔ Created: {doc.name}")

    frappe.db.commit()
    print("--- ✅ SMART IDs ACTIVE ---")

if __name__ == "__main__":
    run()

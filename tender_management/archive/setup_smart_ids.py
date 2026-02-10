import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import add_days, nowdate
import random

def run():
    print("--- 🆔 CONFIGURING SMART TENDER IDs ---")

    # 1. MODIFY DOCTYPE SETTINGS
    if frappe.db.exists("DocType", "Tender Opportunity"):
        doc = frappe.get_doc("DocType", "Tender Opportunity")
        
        # A. Update Sector Options (Adding Maintenance & Water Works)
        new_sectors = "Construction\nElectro-Mechanical\nMaintenance\nWater Works\nGeneral Supply"
        
        # B. Set Autoname to use Naming Series
        doc.autoname = "naming_series:"
        
        for field in doc.fields:
            if field.fieldname == "sector":
                field.options = new_sectors
        
        # C. Add 'naming_series' field if it doesn't exist
        has_ns = any(f.fieldname == 'naming_series' for f in doc.fields)
        if not has_ns:
            doc.append("fields", {
                "fieldname": "naming_series",
                "label": "Naming Series",
                "fieldtype": "Select",
                "options": "T-CON-.YYYY.-\nT-ELEC-.YYYY.-\nT-WAT-.YYYY.-",
                "hidden": 0, # Visible for verification, set to 1 later if needed
                "reqd": 1,
                "insert_before": "tender_number"
            })
            
        doc.save(ignore_permissions=True)
        print("✔ DocType Updated: Naming Series Enabled")

    # 2. INSTALL CLIENT SCRIPT (To automate the selection)
    # This ensures that when a user selects "Construction", the ID automatically becomes T-CON-...
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
    print("✔ Client Script Installed: Auto-assigns ID based on Sector")

    # 3. REGENERATE DATA (With new ID formats)
    frappe.db.sql("DELETE FROM `tabTender Opportunity`")
    
    tenders = [
        {"title": "HQ Office Construction", "sector": "Construction", "prefix": "T-CON-.YYYY.-", "state": "Submitted", "price": 15000000},
        {"title": "Generator Supply 500kVA", "sector": "Electro-Mechanical", "prefix": "T-ELEC-.YYYY.-", "state": "Won", "price": 4500000},
        {"title": "Annual Facility Upkeep", "sector": "Maintenance", "prefix": "T-WAT-.YYYY.-", "state": "Draft", "price": 850000},
        {"title": "City Water Line Expansion", "sector": "Water Works", "prefix": "T-WAT-.YYYY.-", "state": "Approved to Bid", "price": 3000000},
        {"title": "Rural Road Project", "sector": "Construction", "prefix": "T-CON-.YYYY.-", "state": "Lost", "price": 22000000}
    ]

    print("... creating records with new IDs")
    for t in tenders:
        doc = frappe.get_doc({
            "doctype": "Tender Opportunity",
            "title": t["title"],
            "sector": t["sector"],
            "naming_series": t["prefix"], # We explicitly set this for the sample data
            "workflow_state": "Draft",
            "final_bid_price": t["price"],
            "submission_deadline": add_days(nowdate(), 5)
        })
        doc.insert(ignore_permissions=True, ignore_mandatory=True)
        
        # Force Status
        frappe.db.set_value("Tender Opportunity", doc.name, "workflow_state", t["state"])
        print(f"✔ Created: {doc.name} ({t['title']})")

    frappe.db.commit()
    print("--- ✅ SMART IDs ACTIVE ---")

if __name__ == "__main__":
    run()

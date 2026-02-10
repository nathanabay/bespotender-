import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import add_days, nowdate
import json
import random

def run():
    print("--- 🚀 STARTING COMPLETE SYSTEM FIX ---")

    # ==============================================================================
    # 1. FIELD REPAIR (Fixing 'deadline' vs 'submission_deadline')
    # ==============================================================================
    print("... Repairing Fields")
    dt = "Tender Opportunity"
    
    # Check if the old 'deadline' field exists and rename/use it
    if frappe.db.has_column(dt, "deadline") and not frappe.db.has_column(dt, "submission_deadline"):
        # If 'deadline' exists but 'submission_deadline' doesn't, we rename it
        frappe.db.sql(f"ALTER TABLE `tab{dt}` CHANGE `deadline` `submission_deadline` DATE")
        frappe.clear_cache(doctype=dt)
        print("✔ Database Column Renamed: deadline -> submission_deadline")
    
    # Update DocType Metadata to match
    doc = frappe.get_doc("DocType", dt)
    field_found = False
    for f in doc.fields:
        if f.fieldname == "deadline":
            f.fieldname = "submission_deadline"
            f.label = "Submission Deadline"
            field_found = True
        elif f.fieldname == "submission_deadline":
            field_found = True
            
    if not field_found:
        doc.append("fields", {
            "fieldname": "submission_deadline",
            "label": "Submission Deadline",
            "fieldtype": "Date",
            "reqd": 1,
            "insert_after": "sector"
        })
        
    # SETUP SMART ID SERIES
    # We add the naming series options you requested
    doc.autoname = "naming_series:"
    
    # Ensure naming_series field exists
    if not any(f.fieldname == 'naming_series' for f in doc.fields):
        doc.append("fields", {
            "fieldname": "naming_series",
            "label": "Naming Series",
            "fieldtype": "Select",
            "options": "T-CON-.YYYY.-.####\nT-ELEC-.YYYY.-.####\nT-WAT-.YYYY.-.####",
            "hidden": 0,
            "reqd": 1,
            "insert_before": "tender_number"
        })
    else:
        # Update existing options
        for f in doc.fields:
            if f.fieldname == "naming_series":
                f.options = "T-CON-.YYYY.-.####\nT-ELEC-.YYYY.-.####\nT-WAT-.YYYY.-.####"

    # Update Sector Options
    for f in doc.fields:
        if f.fieldname == "sector":
            f.options = "Construction\nElectro-Mechanical\nMaintenance\nWater Works\nGeneral Supply"

    doc.save(ignore_permissions=True)
    print("✔ DocType Repaired & Smart IDs Configured")

    # ==============================================================================
    # 2. CLIENT SCRIPT (Auto-Select ID based on Sector)
    # ==============================================================================
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
            frm.set_value('naming_series', 'T-CON-.YYYY.-.####'); // Default
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

    # ==============================================================================
    # 3. GENERATE DATA (With Valid Fields)
    # ==============================================================================
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
            "workflow_state": "Draft", # Start valid
            "final_bid_price": t["price"],
            "submission_deadline": add_days(nowdate(), t["days"])
        })
        # We assume 'submission_deadline' works now. If fails, script stops, but database rename should have fixed it.
        doc.insert(ignore_permissions=True)
        
        # Force Status Update
        if t["state"] != "Draft":
            frappe.db.set_value("Tender Opportunity", doc.name, "workflow_state", t["state"])
            
        print(f"✔ Created: {doc.name}")

    # ==============================================================================
    # 4. FIX SIDEBAR (Module Config)
    # ==============================================================================
    # Update Module Def
    if not frappe.db.exists("Module Def", "Tender Management"):
        frappe.get_doc({
            "doctype": "Module Def",
            "module_name": "Tender Management",
            "app_name": "tender_management",
            "title": "Tender Management",
            "package": "tender_management"
        }).insert(ignore_permissions=True)

    # Link Workspace
    if frappe.db.exists("Workspace", "Tender Management"):
        ws = frappe.get_doc("Workspace", "Tender Management")
        ws.module = "Tender Management"
        ws.public = 1
        # Re-add shortcuts for deadlines if missing
        ws.content = json.dumps([
            {"type": "header", "data": {"text": "Tender Performance", "level": 2}},
            {"type": "chart", "data": {"chart_name": "SOP Total Bid Value", "col": 12}},
            {"type": "chart", "data": {"chart_name": "SOP Win Ratio", "col": 6}},
            {"type": "header", "data": {"text": "Operational Links", "level": 2}},
            {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "label": "Tender Registry", "icon": "list", "color": "Blue"}},
            {
                "type": "shortcut", 
                "data": {
                    "link_to": "Tender Opportunity", 
                    "label": "Deadlines This Week", 
                    "icon": "calendar", 
                    "color": "Red",
                    "stats_filter": json.dumps({"submission_deadline": ["Timespan", "This Week"]})
                }
            }
        ])
        ws.save(ignore_permissions=True)

    frappe.db.commit()
    print("--- ✅ COMPLETE SYSTEM FIX SUCCESSFUL ---")

if __name__ == "__main__":
    run()

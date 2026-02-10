import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def run():
    print("--- 🔄 CONFIGURING BID SECURITY SYNC ---")

    # 1. ADD 'BANK NAME' TO TENDER OPPORTUNITY
    # The Bid Security DocType requires a Bank Name, so we need it here too.
    if not frappe.db.has_column("Tender Opportunity", "bank_name"):
        create_custom_fields({
            "Tender Opportunity": [
                {"fieldname": "bank_name", "label": "Bank / Insurer", "fieldtype": "Data", "insert_after": "bond_type"}
            ]
        })
        frappe.clear_cache(doctype="Tender Opportunity")
        print("✔ Added 'Bank Name' field to Tender Opportunity")

    # 2. CREATE THE SYNC LOGIC (Server Script)
    script_name = "Auto-Create Bid Security"
    if frappe.db.exists("Server Script", script_name):
        frappe.delete_doc("Server Script", script_name)

    # This Python code runs inside ERPNext whenever you save a Tender
    script_content = """
# Check if Bond Amount is entered
if doc.bond_amount > 0:
    # Check if a Bid Security record already exists for this tender
    existing_security = frappe.db.exists("Bid Security", {"tender": doc.name})
    
    if existing_security:
        # UPDATE existing record
        security = frappe.get_doc("Bid Security", existing_security)
        security.amount = doc.bond_amount
        security.cpo_number = doc.bond_number
        security.expiry_date = doc.bond_expiry
        security.bank = doc.bank_name
        security.status = doc.bond_status
        security.save(ignore_permissions=True)
        frappe.msgprint(f"🔄 Linked Bid Security updated: {security.name}", alert=True)
        
    else:
        # CREATE new record
        # Only create if we have the minimum required info
        if doc.bond_number and doc.bank_name:
            new_security = frappe.get_doc({
                "doctype": "Bid Security",
                "tender": doc.name,
                "amount": doc.bond_amount,
                "cpo_number": doc.bond_number,
                "expiry_date": doc.bond_expiry or frappe.utils.add_days(frappe.utils.nowdate(), 90),
                "bank": doc.bank_name,
                "status": doc.bond_status or "Active"
            })
            new_security.insert(ignore_permissions=True)
            frappe.msgprint(f"✨ New Bid Security created: {new_security.name}")
"""

    frappe.get_doc({
        "doctype": "Server Script",
        "name": script_name,
        "script_type": "DocType Event",
        "reference_doctype": "Tender Opportunity",
        "doctype_event": "After Save",
        "script": script_content
    }).insert(ignore_permissions=True)
    
    frappe.db.commit()
    print("--- ✅ AUTOMATION ACTIVE ---")

if __name__ == "__main__":
    run()

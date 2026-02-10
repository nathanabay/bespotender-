import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def run():
    print("--- 🔄 RE-INSTALLING BID SECURITY SYNC (ROBUST MODE) ---")

    # 1. ENSURE BANK NAME FIELD EXISTS
    # Just in case the previous run missed it
    if not frappe.db.has_column("Tender Opportunity", "bank_name"):
        create_custom_fields({
            "Tender Opportunity": [
                {"fieldname": "bank_name", "label": "Bank / Insurer", "fieldtype": "Data", "insert_after": "bond_type"}
            ]
        })
        print("✔ Verified 'Bank Name' field")

    # 2. INSTALL THE SERVER SCRIPT
    script_name = "Auto-Create Bid Security"
    if frappe.db.exists("Server Script", script_name):
        frappe.delete_doc("Server Script", script_name)

    # The Logic
    script_content = """
# Only run if there is a Bond Amount
if doc.bond_amount and doc.bond_amount > 0:
    
    # VALIDATION: Don't let them save without a Bank Name if they want a Bond
    if not doc.bank_name:
        frappe.throw("⛔ You entered a Bond Amount but missing the 'Bank / Insurer'. Please fill it in the Bid Bond Details section.")
    if not doc.bond_number:
        frappe.throw("⛔ Missing 'Bond Number' (CPO Ref). Please fill it.")

    # CHECK EXISTING
    existing = frappe.db.get_value("Bid Security", {"tender": doc.name}, "name")

    if existing:
        # UPDATE
        security = frappe.get_doc("Bid Security", existing)
        security.amount = doc.bond_amount
        security.cpo_number = doc.bond_number
        security.expiry_date = doc.bond_expiry
        security.bank = doc.bank_name
        security.status = doc.bond_status
        security.save(ignore_permissions=True)
        frappe.msgprint(f"🔄 CPO {doc.bond_number} updated in Security Registry.", alert=True)
    else:
        # CREATE
        new_sec = frappe.get_doc({
            "doctype": "Bid Security",
            "tender": doc.name,
            "amount": doc.bond_amount,
            "cpo_number": doc.bond_number,
            "expiry_date": doc.bond_expiry or frappe.utils.add_days(frappe.utils.nowdate(), 30),
            "bank": doc.bank_name,
            "status": doc.bond_status or "Active"
        })
        new_sec.insert(ignore_permissions=True)
        frappe.msgprint(f"✨ Bid Security Created: {new_sec.name}", alert=True)
"""

    doc = frappe.get_doc({
        "doctype": "Server Script",
        "name": script_name,
        "script_type": "DocType Event",
        "reference_doctype": "Tender Opportunity",
        "doctype_event": "After Save",
        "script": script_content
    })
    doc.insert(ignore_permissions=True)
    
    frappe.db.commit()
    print("--- ✅ SYNC LOGIC INSTALLED ---")

if __name__ == "__main__":
    run()

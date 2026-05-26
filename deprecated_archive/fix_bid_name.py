import frappe

def run():
    print("--- 🆔 SYNCING BID SECURITY NAMES ---")

    # 1. UPDATE DOCTYPE CONFIGURATION
    if frappe.db.exists("DocType", "Bid Security"):
        doc = frappe.get_doc("DocType", "Bid Security")
        
        # Set ID to be exactly the same as the 'tender' link field
        doc.autoname = "field:tender"
        
        doc.save(ignore_permissions=True)
        print("✔ DocType Updated: Bid Security ID = Tender Name")

    # 2. CLEAR OLD DATA
    # Old IDs (BS-xxxx) are now invalid
    frappe.db.sql("DELETE FROM `tabBid Security`")
    print("✔ Old Security records cleared")

    # 3. REGENERATE RECORDS FROM EXISTING TENDERS
    # We loop through all tenders that have bond info and recreate the security record
    tenders = frappe.get_all("Tender Opportunity", 
                             filters={"bond_amount": [">", 0]}, 
                             fields=["name", "bond_amount", "bond_number", "bond_expiry", "bank_name", "bond_status"])
    
    print(f"... Regenerating Bonds for {len(tenders)} Tenders")
    
    count = 0
    for t in tenders:
        # Only create if we have the basics
        if t.bond_number:
            # Check if Bank Name is missing (common from previous steps)
            bank = t.bank_name if t.bank_name else "Pending Bank"
            
            try:
                new_sec = frappe.get_doc({
                    "doctype": "Bid Security",
                    "tender": t.name,  # THIS BECOMES THE ID
                    "amount": t.bond_amount,
                    "cpo_number": t.bond_number,
                    "expiry_date": t.bond_expiry or frappe.utils.add_days(frappe.utils.nowdate(), 30),
                    "bank": bank,
                    "status": t.bond_status or "Active"
                })
                new_sec.insert(ignore_permissions=True)
                count += 1
                print(f"   ✔ Created: {new_sec.name}")
            except frappe.DuplicateEntryError:
                print(f"   ⚠️ Skipped Duplicate: {t.name}")

    frappe.db.commit()
    print(f"--- ✅ COMPLETED: {count} BONDS SYNCED ---")

if __name__ == "__main__":
    run()

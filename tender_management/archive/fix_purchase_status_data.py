import frappe

def run():
    print("--- 🔧 FIXING INVALID PURCHASE STATUS DATA ---")

    # 1. UPDATE OLD 'Pending' TO 'Pending Assignment'
    # This aligns old data with the new Select options
    frappe.db.sql("""
        UPDATE `tabTender Opportunity`
        SET doc_purchase_status = 'Pending Assignment'
        WHERE doc_purchase_status = 'Pending' OR doc_purchase_status IS NULL OR doc_purchase_status = ''
    """)
    
    frappe.db.commit()
    print("✔ Updated all 'Pending' records to 'Pending Assignment'")

    # 2. UPDATE DOCTYPE DEFAULT
    # Ensure new records start correctly
    dt = "Tender Opportunity"
    if frappe.db.exists("DocType", dt):
        field = frappe.get_doc("DocField", {"parent": dt, "fieldname": "doc_purchase_status"})
        field.default = "Pending Assignment"
        field.save()
        print("✔ Set default value to 'Pending Assignment'")

    print("--- ✅ REPAIR COMPLETE ---")

if __name__ == "__main__":
    run()

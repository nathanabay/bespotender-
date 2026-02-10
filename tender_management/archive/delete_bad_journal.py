import frappe

def run():
    print("--- 🗑️ CLEANING UP BROKEN JOURNAL ENTRY ---")

    # The ID from your error message
    bad_je = "ACC-JV-2026-00002"

    if frappe.db.exists("Journal Entry", bad_je):
        doc = frappe.get_doc("Journal Entry", bad_je)
        
        # Only delete if it's a Draft (docstatus=0)
        if doc.docstatus == 0:
            frappe.delete_doc("Journal Entry", bad_je)
            print(f"✔ Deleted broken draft: {bad_je}")
        else:
            print(f"⚠ Cannot delete {bad_je} because it is already submitted.")
    else:
        print(f"ℹ Journal Entry {bad_je} not found (already deleted).")

    print("--- ✅ READY TO TRY AGAIN ---")

if __name__ == "__main__":
    run()

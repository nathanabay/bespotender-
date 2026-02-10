import frappe

def run():
    print("--- 📑 FINALIZING SIDEBAR CONFIGURATION ---")

    # 1. CREATE MODULE DEFINITION
    # This acts as the "Container" for the sidebar entry
    if not frappe.db.exists("Module Def", "Tender Management"):
        doc = frappe.get_doc({
            "doctype": "Module Def",
            "module_name": "Tender Management",
            "app_name": "tender_management",
            "title": "Tender Management",
            "package": "tender_management"
        })
        doc.insert(ignore_permissions=True)
        print("✔ Module Definition Created")

    # 2. LINK WORKSPACE TO MODULE (Safe Mode)
    ws_name = "Tender Management"
    if frappe.db.exists("Workspace", ws_name):
        # Mandatory Link
        frappe.db.set_value("Workspace", ws_name, "module", "Tender Management")
        frappe.db.set_value("Workspace", ws_name, "public", 1)
        
        # Optional: Try to set category only if column exists
        if frappe.db.has_column("Workspace", "category"):
            frappe.db.set_value("Workspace", ws_name, "category", "Modules")
            
        print("✔ Workspace linked to Module")

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ CONFIGURATION COMPLETE ---")

if __name__ == "__main__":
    run()

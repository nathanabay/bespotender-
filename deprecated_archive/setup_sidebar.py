import frappe

def run():
    print("--- 📑 CONFIGURING SIDEBAR MODULE ---")

    # 1. CREATE/UPDATE MODULE DEFINITION
    # This tells ERPNext that "Tender Management" is a primary app module
    if not frappe.db.exists("Module Def", "Tender Management"):
        doc = frappe.get_doc({
            "doctype": "Module Def",
            "module_name": "Tender Management",
            "app_name": "tender_management",
            "category": "Modules",
            "title": "Tender Management",
            "description": "Construction Bid and Bond Management",
            "package": "tender_management"
        })
        doc.insert(ignore_permissions=True)
        print("✔ Module Definition Created")
    else:
        print("✔ Module Definition already exists")

    # 2. ENSURE WORKSPACE IS LINKED TO MODULE
    ws_name = "Tender Management"
    if frappe.db.exists("Workspace", ws_name):
        frappe.db.set_value("Workspace", ws_name, "module", "Tender Management")
        frappe.db.set_value("Workspace", ws_name, "category", "Modules")
        frappe.db.set_value("Workspace", ws_name, "public", 1)
        # Force standard-like behavior
        frappe.db.set_value("Workspace", ws_name, "is_standard", 0) 
        print("✔ Workspace linked to Module")

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ SIDEBAR CONFIGURATION COMPLETE ---")

if __name__ == "__main__":
    run()

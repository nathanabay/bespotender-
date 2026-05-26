import frappe

def run():
    print("--- 🚑 SYSTEM RESCUE INITIATED ---")

    user = "nathanamare@bespo.et"

    # 1. FORCE MODULE VISIBILITY
    # Sometimes the module is "unchecked" in User Settings, making the screen blank.
    user_doc = frappe.get_doc("User", user)
    block_modules = user_doc.get("block_modules") or []
    if "Tender Management" in block_modules:
        user_doc.block_modules = [m for m in block_modules if m != "Tender Management"]
        user_doc.save(ignore_permissions=True)
        print("✔ Fixed: Module was hidden, now visible.")
    else:
        print("✔ Module visibility is OK.")

    # 2. FIX WORKSPACE PERMISSIONS
    # If you can't "Read" a Workspace, you get a blank page.
    # We add 'Workspace' access to the 'Tender Manager' role.
    if frappe.db.exists("DocType", "Workspace"):
        frappe.db.sql("DELETE FROM `tabCustom DocPerm` WHERE parent='Workspace' AND role='Tender Manager'")
        
        frappe.get_doc({
            "doctype": "Custom DocPerm",
            "parent": "Workspace",
            "parenttype": "DocType",
            "parentfield": "permissions",
            "role": "Tender Manager",
            "read": 1, "write": 1, "create": 0, "delete": 0,
            "permlevel": 0
        }).insert(ignore_permissions=True)
        print("✔ Fixed: Workspace permissions granted to Tender Manager.")

    # 3. TEMPORARILY DISABLE CLIENT SCRIPTS
    # A bad Javascript line can crash the whole desk. We disable them to check.
    frappe.db.sql("UPDATE `tabClient Script` SET enabled=0 WHERE module='Tender Management'")
    print("✔ Disabled Client Scripts (Safety Check).")

    # 4. RESET MODULE DEF
    # Ensure the app linkage is correct
    if frappe.db.exists("Module Def", "Tender Management"):
        mod = frappe.get_doc("Module Def", "Tender Management")
        mod.app_name = "tender_management"
        mod.save(ignore_permissions=True)
        print("✔ Refreshed Module Definition.")

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ RESCUE COMPLETE: TRY LIST VIEW NOW ---")

if __name__ == "__main__":
    run()

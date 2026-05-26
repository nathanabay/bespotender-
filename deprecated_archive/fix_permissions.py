import frappe

def run():
    print("--- 🔐 FIXING PERMISSIONS & ROLES ---")

    # 1. CREATE ROLES (If missing)
    roles = ["Tender Manager", "Tender User"]
    for role in roles:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)
            print(f"✔ Role Created: {role}")

    # 2. DEFINE DOCTYPES TO FIX
    # These are the new features we added that likely have empty permission tables
    doctypes = [
        "Tender Opportunity", 
        "Tender Content Library", 
        "Tender Competitor", 
        "Tender Requirement", 
        "Tender Bid",
        "Tender Evaluation Criteria",
        "Tender Document Checklist",
        "Bid Security"
    ]

    # 3. GRANT PERMISSIONS
    for dt in doctypes:
        if frappe.db.exists("DocType", dt):
            # A. Clear old permissions to avoid duplicates
            frappe.db.sql("DELETE FROM `tabCustom DocPerm` WHERE parent=%s", (dt,))
            
            # B. Add "Tender Manager" (Full Access)
            frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": dt,
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": "Tender Manager",
                "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "amend": 1,
                "permlevel": 0
            }).insert(ignore_permissions=True)

            # C. Add "Tender User" (Restricted Access)
            frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": dt,
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": "Tender User",
                "read": 1, "write": 1, "create": 1, "delete": 0,
                "permlevel": 0
            }).insert(ignore_permissions=True)
            
            # D. Ensure System Manager has access too
            frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": dt,
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": "System Manager",
                "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1,
                "permlevel": 0
            }).insert(ignore_permissions=True)

            print(f"✔ Permissions granted for: {dt}")

    # 4. ASSIGN ROLE TO YOU
    user = "nathanamare@bespo.et"
    if frappe.db.exists("User", user):
        user_doc = frappe.get_doc("User", user)
        
        # Check if role already exists
        has_role = False
        for r in user_doc.roles:
            if r.role == "Tender Manager":
                has_role = True
                break
        
        if not has_role:
            user_doc.append("roles", {"role": "Tender Manager"})
            user_doc.save(ignore_permissions=True)
            print(f"✔ Assigned 'Tender Manager' role to {user}")
        else:
            print(f"✔ User {user} already has 'Tender Manager' role")
    else:
        print(f"⚠️ User {user} not found. Please assign 'Tender Manager' role manually.")

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ ACCESS RESTORED: PLEASE RELOAD ---")

if __name__ == "__main__":
    run()

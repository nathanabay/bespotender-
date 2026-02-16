import frappe

def fix_dashboard_links():
    print("--- 🔍 Auditing Dashboard Links for Tender Opportunity ---")
    
    # 1. Check for database-level Link records
    links = frappe.get_all("DocType Link", 
                          filters={"parent": "Tender Opportunity"}, 
                          fields=["name", "link_doctype", "link_fieldname"])
    
    if not links:
        print("✔ No database-level overrides found in 'DocType Link'.")
    else:
        print(f"⚠ Found {len(links)} database-level overrides:")
        for l in links:
            print(f"  - {l.link_doctype} (linked via {l.link_fieldname})")
            
            # Delete if it's Document Template (which doesn't have a tender field)
            if l.link_doctype == "Document Template" or l.link_doctype == "Tender Comment":
                print(f"    🔥 DELETING invalid link: {l.link_doctype}")
                frappe.delete_doc("DocType Link", l.name, force=True)

    # 2. Check for Dashboard Charts that might be forcing a count
    # (Sometimes charts on a dashboard can trigger these calls)
    charts = frappe.get_all("Dashboard Chart", filters={"document_type": "Document Template"})
    if charts:
        print(f"⚠ Found {len(charts)} charts for Document Template. If these are on the Tender dashboard, they might cause issues.")

    # 3. Clear Cache
    frappe.db.commit()
    frappe.clear_cache(doctype="Tender Opportunity")
    print("--- ✅ Repair Complete ---")

if __name__ == "__main__":
    fix_dashboard_links()

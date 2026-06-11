"""
tender_management/tender_management/setup/cleanup.py

NUCLEAR OPTION: Disable any database-stored customizations that might interfere.
Specifically targets the ghost "Bond Number and Bank Name are required" validation.
"""
import frappe


def cleanup_legacy_customizations():
	print("🧹 Cleaning up legacy customizations...")
	
	target_doctype = "Tender Opportunity"
	
	# 1. Disable ALL Server Scripts for Tender Opportunity except our managed one
	managed_scripts = ["Auto Payment Entry - Document Purchase"]
	
	server_scripts = frappe.get_all("Server Script", filters={
		"reference_doctype": target_doctype,
		"disabled": 0
	}, fields=["name"])
	
	for s in server_scripts:
		if s.name not in managed_scripts:
			frappe.db.set_value("Server Script", s.name, "disabled", 1)
			print(f"  ✔ Disabled legacy Server Script: {s.name}")
			
	# 2. Disable ANY database-stored Client Scripts for Tender Opportunity
	# These often override the file-based .js script
	client_scripts = frappe.get_all("Client Script", filters={
		"dt": target_doctype,
		"enabled": 1
	}, fields=["name"])
	
	for c in client_scripts:
		frappe.db.set_value("Client Script", c.name, "enabled", 0)
		print(f"  ✔ Disabled legacy Client Script: {c.name}")
		
	# 3. Delete Property Setters that force bond_number or bank_name
	frappe.db.sql("""
		DELETE FROM `tabProperty Setter` 
		WHERE doc_type = %s 
		AND field_name IN ('bond_number', 'bank_name')
		AND property = 'reqd'
	""", (target_doctype))
	print("  ✔ Cleared mandatory Property Setters for bond fields")
	
	# 4. Delete persistent Dashboard Links (DocType Link) that cause SQL errors
	# Document Template and Tender Comment don't have a 'tender' field and shouldn't be here
	invalid_links = ["Document Template", "Tender Comment"]
	frappe.db.sql("""
		DELETE FROM `tabDocType Link` 
		WHERE parent = %s 
		AND link_doctype IN (%s)
	""" % ("%s", ", ".join(["%s"] * len(invalid_links))), [target_doctype] + invalid_links)
	print(f"  ✔ Cleared invalid DocType Links: {', '.join(invalid_links)}")

	# 5. Fix any links using the old fieldname 'tender_opportunity'
	frappe.db.sql("""
		UPDATE `tabDocType Link` 
		SET link_fieldname = 'tender' 
		WHERE parent = %s 
		AND link_fieldname = 'tender_opportunity'
	""", (target_doctype))

	frappe.clear_cache(doctype=target_doctype)
	print(f"  ✔ Cache cleared for {target_doctype}")

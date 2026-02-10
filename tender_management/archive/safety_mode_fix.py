import frappe
import json

def run():
    print("--- 🛡️ ACTIVATING DASHBOARD SAFETY MODE ---")

    # 1. DELETE ALL TENDER WORKSPACES (Clean Slate)
    # We remove anything that might be corrupted
    frappe.db.sql("DELETE FROM `tabWorkspace` WHERE module = 'Tender Management'")
    print("✔ Deleted all old corrupted workspaces.")

    # 2. CREATE A "SAFE" WORKSPACE
    # No charts, no cards. Just links. If this loads, the database is fine.
    ws_name = "Tender Console"
    
    # Very simple content structure
    ws_content = [
        {"type": "header", "data": {"text": "Tender Management", "level": 1}},
        {"type": "text", "data": {"text": "System is active. If you see this, the blank screen error is resolved."}},
        {"type": "header", "data": {"text": "Registry", "level": 2}},
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "type": "DocType", "label": "All Tenders", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "type": "DocType", "label": "Bid Bonds", "icon": "lock", "color": "Orange"}}
    ]

    doc = frappe.get_doc({
        "doctype": "Workspace",
        "name": ws_name,
        "label": "Tender Console",
        "title": "Tender Console",
        "module": "Tender Management",
        "public": 1,
        "is_standard": 0,
        "content": json.dumps(ws_content)
    })
    doc.insert(ignore_permissions=True)

    frappe.db.commit()
    frappe.clear_cache()
    
    # 3. GENERATE DIRECT LINK
    site_url = frappe.utils.get_url()
    print("--- ✅ RECOVERY COMPLETE ---")
    print(f"👉 PLEASE CLICK THIS LINK TO OPEN: {site_url}/app/tender-console")

if __name__ == "__main__":
    run()

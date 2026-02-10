import frappe
import json

def run():
    print("--- 🚀 MASTER REBUILD: TENDER WORKSPACE ---")

    # 1. Clean up potential duplicates or broken states
    workspace_name = "Tender Management"
    if frappe.db.exists("Workspace", workspace_name):
        frappe.delete_doc("Workspace", workspace_name, ignore_missing=True, force=True)
        print(f"🗑 Old workspace deleted.")

    # 2. Define fresh content with explicit 'label' and 'type' attributes
    ws_content = [
        {"type": "header", "data": {"text": "Tender Performance Overview", "level": 2}},
        {"type": "chart", "data": {"chart_name": "Tender Pipeline Value", "col": 12}},
        {"type": "chart", "data": {"chart_name": "Win Loss Ratio", "col": 12}},
        {"type": "header", "data": {"text": "Tender Registry", "level": 2}},
        {"type": "link", "data": {"link_to": "Tender Opportunity", "link_type": "DocType", "label": "All Tender Opportunities"}},
        {"type": "link", "data": {"link_to": "Bid Security", "link_type": "DocType", "label": "CPO Tracking / Bid Bonds"}}
    ]

    # 3. Create the new workspace with 'public' and 'is_standard' flags
    doc = frappe.get_doc({
        "doctype": "Workspace",
        "name": workspace_name,
        "label": workspace_name,
        "title": workspace_name,
        "category": "Modules",
        "module": "Tender Management",
        "icon": "folder",
        "public": 1,
        "is_standard": 0, # Setting to 0 ensures it's treated as a custom site-specific workspace
        "content": json.dumps(ws_content)
    })
    
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ MASTER REBUILD COMPLETE ---")

run()

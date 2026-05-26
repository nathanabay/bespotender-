import frappe
import json

def run():
    print("--- 🛠 FORCING DASHBOARD VISIBILITY ---")

    # 1. Update Workspace with explicit Card and Chart Data
    workspace_name = "Tender Management"
    
    # We define the content with explicit 'label' and 'name' for charts
    ws_content = [
        {"type": "header", "data": {"text": "Tender Performance Overview", "level": 2}},
        {"type": "chart", "data": {"chart_name": "Tender Pipeline Value", "col": 12}},
        {"type": "chart", "data": {"chart_name": "Win Loss Ratio", "col": 12}},
        {"type": "header", "data": {"text": "Tender Actions", "level": 2}},
        {"type": "link", "data": {"link_to": "Tender Opportunity", "link_type": "DocType", "label": "Tender Registry", "dependencies": []}},
        {"type": "link", "data": {"link_to": "Bid Security", "link_type": "DocType", "label": "CPO Management", "dependencies": []}}
    ]

    if frappe.db.exists("Workspace", workspace_name):
        doc = frappe.get_doc("Workspace", workspace_name)
        doc.content = json.dumps(ws_content)
        doc.is_standard = 0  # Force to 0 so it's treated as a custom user workspace
        doc.public = 1
        doc.module = "Tender Management"
        doc.save(ignore_permissions=True)
        print(f"✔ Workspace '{workspace_name}' Updated")

    # 2. Force Chart Permissions
    for chart in ["Tender Pipeline Value", "Win Loss Ratio"]:
        if frappe.db.exists("Dashboard Chart", chart):
            frappe.db.set_value("Dashboard Chart", chart, "is_public", 1)
            frappe.db.set_value("Dashboard Chart", chart, "is_standard", 0)
            print(f"✔ Chart '{chart}' set to Public")

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ SYSTEM FORCED: PLEASE RELOAD BROWSER ---")

run()

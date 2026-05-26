import frappe
import json

def run():
    print("--- 🔓 UNLOCKING BLANK WORKSPACE ---")
    ws_name = "Tender Management"

    # 1. DELETE USER CUSTOMIZATIONS (The likely culprit)
    # This deletes any "personal" edits users might have made that resulted in a blank screen
    frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name = %s AND is_standard = 0 AND public = 0", (ws_name,))
    
    # 2. RE-DEFINE THE MASTER WORKSPACE
    if frappe.db.exists("Workspace", ws_name):
        frappe.delete_doc("Workspace", ws_name, force=True)

    # 3. DEFINE CONTENT (SOP Section 5 Structure)
    ws_content = [
        {"type": "header", "data": {"text": "Tender Performance (SOP)", "level": 2}},
        {"type": "chart", "data": {"chart_name": "SOP Total Bid Value", "col": 12}},
        {"type": "chart", "data": {"chart_name": "SOP Win Ratio", "col": 6}},
        {"type": "chart", "data": {"chart_name": "SOP Bond Exposure", "col": 6}},
        {"type": "header", "data": {"text": "Operational Links", "level": 2}},
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "label": "All Tenders", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "label": "Bid Bonds", "icon": "lock", "color": "Orange"}},
        {"type": "shortcut", "data": {"link_to": "Payment Entry", "label": "Tender Fees", "icon": "credit-card", "color": "Green"}}
    ]

    # 4. INSERT AS PUBLIC
    doc = frappe.get_doc({
        "doctype": "Workspace",
        "name": ws_name,
        "label": ws_name,
        "title": ws_name,
        "category": "Modules",
        "module": "Tender Management",
        "public": 1, 
        "is_standard": 0, # Force as Custom-Public to avoid Standard restrictions
        "content": json.dumps(ws_content)
    })
    doc.insert(ignore_permissions=True)

    # 5. FORCE CHARTS TO BE PUBLIC
    charts = ["SOP Total Bid Value", "SOP Win Ratio", "SOP Bond Exposure"]
    for c in charts:
        if frappe.db.exists("Dashboard Chart", c):
            frappe.db.set_value("Dashboard Chart", c, "is_public", 1)

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ WORKSPACE RESET: PLEASE RELOAD ---")

if __name__ == "__main__":
    run()

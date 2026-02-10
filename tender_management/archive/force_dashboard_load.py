import frappe
import json

def run():
    print("--- 🚀 FORCING TENDER DASHBOARD LOAD ---")
    ws_name = "Tender Management"

    # 1. DELETE PERSONAL CUSTOMIZATIONS (The #1 Cause of Blank Screens)
    # This deletes any "private" version of the workspace that belongs to you or Administrator
    frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name = %s AND public = 0", (ws_name,))
    print("✔ Deleted cached/personal blank views.")

    # 2. ENSURE CHARTS EXIST AND ARE PUBLIC
    charts = ["SOP Total Bid Value", "SOP Win Ratio", "SOP Bond Exposure"]
    for c in charts:
        if frappe.db.exists("Dashboard Chart", c):
            frappe.db.set_value("Dashboard Chart", c, "is_public", 1)
        else:
            print(f"⚠️ Warning: Chart '{c}' missing! (Will require data regen)")

    # 3. DEFINE THE DASHBOARD CONTENT
    # This JSON structure tells the browser exactly what widgets to render
    dashboard_content = [
        {"type": "header", "data": {"text": "Tender Opportunity Dashboard", "level": 2}},
        
        # Row 1: The Main Pipeline Chart
        {"type": "chart", "data": {"chart_name": "SOP Total Bid Value", "col": 12}},
        
        # Row 2: Win Ratio & Bond Exposure
        {"type": "chart", "data": {"chart_name": "SOP Win Ratio", "col": 6}},
        {"type": "chart", "data": {"chart_name": "SOP Bond Exposure", "col": 6}},
        
        {"type": "header", "data": {"text": "Quick Actions", "level": 2}},
        
        # Row 3: Shortcuts
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "label": "Tender Registry", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "label": "Bid Bonds", "icon": "lock", "color": "Orange"}},
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "label": "Deadlines This Week", "icon": "calendar", "color": "Red", "stats_filter": json.dumps({"submission_deadline": ["Timespan", "This Week"]})}}
    ]

    # 4. OVERWRITE THE MAIN WORKSPACE
    if frappe.db.exists("Workspace", ws_name):
        doc = frappe.get_doc("Workspace", ws_name)
        doc.content = json.dumps(dashboard_content)
        doc.public = 1
        doc.title = "Tender Management"
        doc.save(ignore_permissions=True)
        print("✔ Main Workspace Content Injected.")
    else:
        # Create if missing
        doc = frappe.get_doc({
            "doctype": "Workspace",
            "name": ws_name,
            "label": ws_name,
            "title": ws_name,
            "module": "Tender Management",
            "public": 1,
            "content": json.dumps(dashboard_content)
        })
        doc.insert(ignore_permissions=True)
        print("✔ New Workspace Created.")

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ DASHBOARD FORCED: RELOAD YOUR BROWSER ---")

if __name__ == "__main__":
    run()

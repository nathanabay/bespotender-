import frappe
import json

def run():
    print("--- 🔗 FIXING BROKEN LINKS & ROUTING ---")

    # 1. ENSURE DOCTYPE IS VIEWABLE
    # Sometimes custom doctypes are created without the 'in_list_view' settings causing 404s
    dt = "Tender Content Library"
    if frappe.db.exists("DocType", dt):
        doc = frappe.get_doc("DocType", dt)
        doc.has_web_view = 0 # Ensure it's not trying to look for a website page
        doc.is_submittable = 0
        doc.istable = 0
        doc.module = "Tender Management"
        doc.save(ignore_permissions=True)
        print(f"✔ Refreshed metadata for: {dt}")

    # 2. REPAIR WORKSPACE SHORTCUTS
    # We will overwrite the workspace content with guaranteed valid links
    ws_name = "Tender Management"
    
    # Define correct links. Note: type must be 'DocType' for internal lists.
    ws_content = [
        {"type": "header", "data": {"text": "Tender Performance", "level": 2}},
        {"type": "chart", "data": {"chart_name": "SOP Pipeline Value", "col": 12}},
        {"type": "chart", "data": {"chart_name": "SOP Win Ratio", "col": 6}},
        
        {"type": "header", "data": {"text": "Tender Process", "level": 2}},
        # The Critical Fix: Ensure link_to matches the DocType name exactly
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "type": "DocType", "label": "Tender Registry", "icon": "list", "color": "Blue"}},
        {"type": "shortcut", "data": {"link_to": "Tender Bid", "type": "DocType", "label": "Bids Received", "icon": "users", "color": "Purple"}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "type": "DocType", "label": "Bond Tracking", "icon": "lock", "color": "Orange"}},
        
        {"type": "header", "data": {"text": "Knowledge Base", "level": 2}},
        # This is likely the broken link we are fixing
        {"type": "shortcut", "data": {"link_to": "Tender Content Library", "type": "DocType", "label": "Content Library", "icon": "book", "color": "Teal"}},
    ]

    if frappe.db.exists("Workspace", ws_name):
        doc = frappe.get_doc("Workspace", ws_name)
        doc.content = json.dumps(ws_content)
        doc.save(ignore_permissions=True)
        print("✔ Workspace Shortcuts Repaired")

    # 3. CLEAR ROUTING CACHE
    frappe.clear_cache()
    print("--- ✅ REPAIR COMPLETE: RELOAD BROWSER ---")

if __name__ == "__main__":
    run()

import frappe
import json

def run():
    doc = frappe.get_doc("Workspace", "Tender Management")
    
    # Check if already exists
    exists = False
    for s in doc.shortcuts:
        if s.label == "Company Documents":
            exists = True
            break
            
    if not exists:
        doc.append("shortcuts", {
            "label": "Company Documents",
            "link_to": "Bid Document Management",
            "type": "DocType",
            "icon": "folder",
            "color": "Green"
        })
        
        # Also update 'content' field if it exists (Frappe 15 uses this for visual layout)
        if doc.content:
            try:
                content = json.loads(doc.content)
                # Find the Templates shortcut to insert after it
                index = -1
                for i, item in enumerate(content):
                    if item.get("type") == "shortcut" and item.get("data", {}).get("shortcut_name") == "Templates":
                        index = i
                        break
                
                new_shortcut = {"type": "shortcut", "data": {"shortcut_name": "Company Documents", "col": 3}}
                if index != -1:
                    content.insert(index + 1, new_shortcut)
                else:
                    content.append(new_shortcut)
                
                doc.content = json.dumps(content)
            except Exception as e:
                print(f"Failed to update content JSON: {e}")
        
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        print("Successfully updated Tender Management workspace with Company Documents shortcut.")
    else:
        print("Shortcut already exists in workspace.")

if __name__ == "__main__":
    run()

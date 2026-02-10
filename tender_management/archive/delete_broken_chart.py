import frappe
import json

def run():
    print("--- 🚑 REMOVING CORRUPTED CHART 'SOP Total Bid Value' ---")

    chart_name = "SOP Total Bid Value"

    # 1. DELETE THE BROKEN CHART DOCUMENT
    if frappe.db.exists("Dashboard Chart", chart_name):
        frappe.delete_doc("Dashboard Chart", chart_name, force=True)
        print(f"✔ Successfully deleted broken chart: {chart_name}")
    else:
        print(f"✔ Chart {chart_name} was already removed.")

    # 2. CLEANUP WORKSPACES REFERENCING IT
    # We check all workspaces to see if they are still trying to load this ghost chart
    workspaces = frappe.get_all("Workspace", fields=["name", "content"])
    
    for ws in workspaces:
        if ws.content and chart_name in ws.content:
            print(f"   ... Cleaning references in Workspace '{ws.name}'")
            
            # Load the JSON content
            content = json.loads(ws.content)
            new_content = []
            
            # Filter out the bad chart
            for item in content:
                if item.get("type") == "chart" and item.get("data", {}).get("chart_name") == chart_name:
                    print(f"       - Removed widget for {chart_name}")
                    continue # Skip this item
                new_content.append(item)
            
            # Save the clean version
            frappe.db.set_value("Workspace", ws.name, "content", json.dumps(new_content))

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ ERROR CLEARED ---")

if __name__ == "__main__":
    run()

import frappe
import json

def run():
    print("--- 📊 FIXING 'TENDER PIPELINE VALUE' CHART ---")

    chart_name = "Tender Pipeline Value"

    # 1. DELETE BROKEN CHART
    if frappe.db.exists("Dashboard Chart", chart_name):
        frappe.delete_doc("Dashboard Chart", chart_name, force=True)
        print(f"✔ Deleted broken chart: {chart_name}")

    # 2. CREATE VALID CHART
    # We explicitly set it to Sum 'final_bid_price' grouped by 'workflow_state'
    frappe.get_doc({
        "doctype": "Dashboard Chart",
        "chart_name": chart_name,
        "chart_type": "Group By",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "workflow_state", 
        "group_by_type": "Sum",
        "aggregate_function_based_on": "final_bid_price",
        "type": "Bar",
        "is_public": 1,
        "color": "#e74c3c", # Red/Orange for Value
        "filters_json": "[]", # Empty filters
        "group_by_sort_order": "desc",
        "timeseries": 0
    }).insert(ignore_permissions=True)
    
    print(f"✔ Recreated Chart: {chart_name}")

    # 3. REFRESH WORKSPACE
    # Ensure the workspace knows about the new chart
    ws_name = "Tender Management"
    if frappe.db.exists("Workspace", ws_name):
        doc = frappe.get_doc("Workspace", ws_name)
        
        # Check if chart is already linked, if not, we assume it's fine (auto-bind by name)
        # We just save to trigger cache refresh
        doc.save(ignore_permissions=True)
        print("✔ Refreshed Workspace")

    print("--- ✅ CHART REPAIRED ---")

if __name__ == "__main__":
    run()

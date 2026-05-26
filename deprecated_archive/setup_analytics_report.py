import frappe
import os
import json

def run():
    print("--- 📈 DEPLOYING STRATEGIC ANALYTICS REPORT ---")

    # 1. DEFINE PATHS
    app_path = frappe.get_app_path("tender_management")
    report_dir = os.path.join(app_path, "report", "strategic_tender_analytics")
    
    # Create Directory
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
        print(f"✔ Created Directory: {report_dir}")

    # 2. CREATE __init__.py
    with open(os.path.join(report_dir, "__init__.py"), "w") as f:
        f.write("")

    # 3. CREATE JAVASCRIPT FILE (.js) - FILTERS
    js_content = """
frappe.query_reports["Strategic Tender Analytics"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -12),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "sector",
            "label": __("Sector"),
            "fieldtype": "Select",
            "options": "\nConstruction\nElectro-Mechanical\nMaintenance\nWater Works\nGeneral Supply"
        }
    ]
};
"""
    with open(os.path.join(report_dir, "strategic_tender_analytics.js"), "w") as f:
        f.write(js_content)
    print("✔ Written JS Filters")

    # 4. CREATE PYTHON FILE (.py) - LOGIC & CHARTS
    py_content = """
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    # Generate Analytics
    chart = get_chart_data(data)
    report_summary = get_report_summary(data)
    
    return columns, data, None, chart, report_summary

def get_columns():
    return [
        {"label": _("Sector"), "fieldname": "sector", "fieldtype": "Data", "width": 150},
        {"label": _("Total Bids"), "fieldname": "total_bids", "fieldtype": "Int", "width": 100},
        {"label": _("Won"), "fieldname": "won_bids", "fieldtype": "Int", "width": 80},
        {"label": _("Lost"), "fieldname": "lost_bids", "fieldtype": "Int", "width": 80},
        {"label": _("Win Rate (%)"), "fieldname": "win_rate", "fieldtype": "Percent", "width": 100},
        {"label": _("Total Bid Value"), "fieldname": "total_value", "fieldtype": "Currency", "width": 150},
        {"label": _("Avg Margin"), "fieldname": "avg_margin", "fieldtype": "Currency", "width": 120}
    ]

def get_data(filters):
    conditions = ""
    if filters.get("sector"):
        conditions += f" AND sector = '{filters.get('sector')}'"
        
    # Fetch Raw Data
    sql = f'''
        SELECT 
            sector,
            COUNT(name) as total_bids,
            SUM(CASE WHEN workflow_state = 'Won' THEN 1 ELSE 0 END) as won_bids,
            SUM(CASE WHEN workflow_state = 'Lost' THEN 1 ELSE 0 END) as lost_bids,
            SUM(final_bid_price) as total_value,
            AVG(final_bid_price - estimated_cost) as avg_margin
        FROM `tabTender Opportunity`
        WHERE submission_deadline BETWEEN '{filters.get("from_date")}' AND '{filters.get("to_date")}'
        {conditions}
        GROUP BY sector
    '''
    raw_data = frappe.db.sql(sql, as_dict=True)
    
    # Process for View
    for row in raw_data:
        if row.total_bids > 0:
            row.win_rate = (row.won_bids / row.total_bids) * 100
        else:
            row.win_rate = 0
            
    return raw_data

def get_chart_data(data):
    labels = [row.get("sector") for row in data]
    
    # We want a Multi-Bar chart (Won vs Lost)
    won_values = [row.get("won_bids") for row in data]
    lost_values = [row.get("lost_bids") for row in data]

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Won", "values": won_values},
                {"name": "Lost", "values": lost_values}
            ]
        },
        "type": "bar",
        "colors": ["#2ecc71", "#e74c3c"]
    }

def get_report_summary(data):
    total_won = sum([d.get("won_bids") for d in data])
    total_val = sum([d.get("total_value") for d in data])
    
    avg_win_rate = 0
    if data:
        avg_win_rate = sum([d.get("win_rate") for d in data]) / len(data)

    return [
        {"value": total_won, "label": "Total Wins", "indicator": "Green", "datatype": "Int"},
        {"value": avg_win_rate, "label": "Avg Win Rate", "indicator": "Blue", "datatype": "Percent"},
        {"value": total_val, "label": "Total Pipeline Value", "indicator": "Orange", "datatype": "Currency"}
    ]
"""
    with open(os.path.join(report_dir, "strategic_tender_analytics.py"), "w") as f:
        f.write(py_content)
    print("✔ Written Python Logic (Charts & Summary)")

    # 5. CREATE JSON METADATA
    json_content = json.dumps({
        "module": "Tender Management",
        "ref_doctype": "Tender Opportunity",
        "report_name": "Strategic Tender Analytics",
        "report_type": "Script Report",
        "is_standard": "Yes",
        "disabled": 0
    }, indent=4)
    
    with open(os.path.join(report_dir, "strategic_tender_analytics.json"), "w") as f:
        f.write(json_content)
    print("✔ Written Metadata")

    # 6. REGISTER IN DATABASE
    if not frappe.db.exists("Report", "Strategic Tender Analytics"):
        doc = frappe.get_doc({
            "doctype": "Report",
            "report_name": "Strategic Tender Analytics",
            "report_type": "Script Report",
            "is_standard": "Yes",
            "module": "Tender Management",
            "ref_doctype": "Tender Opportunity"
        })
        doc.insert(ignore_permissions=True)
        print("✔ Registered Report in Database")
    
    frappe.db.commit()
    print("--- ✅ REPORT DEPLOYED SUCCESSFULLY ---")

if __name__ == "__main__":
    run()

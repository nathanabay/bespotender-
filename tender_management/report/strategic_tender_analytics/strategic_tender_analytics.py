import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
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
    values = {}
    conditions = []

    if filters.get("from_date"):
        conditions.append("submission_deadline >= %(from_date)s")
        values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("submission_deadline <= %(to_date)s")
        values["to_date"] = filters["to_date"]
    if filters.get("sector"):
        conditions.append("sector = %(sector)s")
        values["sector"] = filters["sector"]

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    raw_data = frappe.db.sql("""
        SELECT
            sector,
            COUNT(name) as total_bids,
            SUM(CASE WHEN workflow_state = 'Won' THEN 1 ELSE 0 END) as won_bids,
            SUM(CASE WHEN workflow_state = 'Lost' THEN 1 ELSE 0 END) as lost_bids,
            SUM(final_bid_price) as total_value,
            AVG(final_bid_price - estimated_cost) as avg_margin
        FROM `tabTender Opportunity`
        WHERE {where}
        GROUP BY sector
    """.format(where=where_clause), values, as_dict=True)

    for row in raw_data:
        if row.total_bids > 0:
            row.win_rate = (row.won_bids / row.total_bids) * 100
        else:
            row.win_rate = 0

    return raw_data

def get_chart_data(data):
    labels = [row.get("sector") for row in data]
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

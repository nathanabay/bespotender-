
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
            "options": "
Construction
Electro-Mechanical
Maintenance
Water Works
General Supply"
        }
    ]
};

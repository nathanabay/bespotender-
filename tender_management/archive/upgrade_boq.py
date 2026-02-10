import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def run():
    print("--- 🛠 UPGRADING BOQ TABLE WITH MORE COLUMNS ---")

    # We add these columns to the Child Table "Tender BOQ Item"
    fields = {
        "Tender BOQ Item": [
            {
                "fieldname": "brand",
                "label": "Brand / Make",
                "fieldtype": "Data",
                "insert_after": "description",
                "columns": 2
            },
            {
                "fieldname": "origin",
                "label": "Country of Origin",
                "fieldtype": "Data",
                "insert_after": "brand",
                "columns": 1
            },
            {
                "fieldname": "supplier",
                "label": "Potential Supplier",
                "fieldtype": "Link",
                "options": "Supplier",
                "insert_after": "origin",
                "columns": 2
            },
            {
                "fieldname": "remarks",
                "label": "Internal Remarks",
                "fieldtype": "Small Text",
                "insert_after": "amount"
            }
        ]
    }

    create_custom_fields(fields)
    print("✔ Added Columns: Brand, Origin, Supplier, Remarks")
    
    frappe.clear_cache()
    print("--- ✅ BOQ UPGRADE COMPLETE ---")

import frappe
from frappe.utils import now_datetime, add_to_date
def run():
    ten_minutes_ago = add_to_date(now_datetime(), minutes=-60) # Try 60 minutes
    errors = frappe.get_all("Error Log", 
        fields=["error", "creation", "method"], 
        filters={"creation": [">", ten_minutes_ago]},
        order_by="creation desc", limit=20)
    
    print(f"Checking for errors after {ten_minutes_ago}")
    if not errors:
        print("No errors found in the database for the last hour.")
        # Check all logs again just in case
        latest = frappe.get_all("Error Log", fields=["creation"], order_by="creation desc", limit=1)
        if latest:
            print(f"Latest error in DB is from: {latest[0].creation}")
    
    for e in errors:
        print("="*50)
        print(f"CREATED AT: {e.creation}")
        print(f"METHOD: {e.method}")
        print(e.error)
        print("="*50)

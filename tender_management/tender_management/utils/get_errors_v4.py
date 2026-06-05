import frappe
from frappe.utils import today
def run():
    errors = frappe.get_all("Error Log", 
        fields=["error", "creation", "method"], 
        filters={"creation": [">", today()]},
        order_by="creation desc", limit=20)
    for e in errors:
        print("="*50)
        print(f"CREATED AT: {e.creation}")
        print(f"METHOD: {e.method}")
        print(e.error)
        print("="*50)

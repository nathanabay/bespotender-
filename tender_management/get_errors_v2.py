import frappe
def run():
    errors = frappe.get_all("Error Log", fields=["error", "creation"], order_by="creation desc", limit=5)
    for e in errors:
        print("="*50)
        print(f"CREATED AT: {e.creation}")
        print(e.error)
        print("="*50)

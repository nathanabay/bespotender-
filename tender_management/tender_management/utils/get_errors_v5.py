import frappe
def run():
    errors = frappe.get_all("Error Log", 
        fields=["error", "creation", "method"], 
        order_by="creation desc", limit=50)
    for e in errors:
        print("="*50)
        print(f"CREATED AT: {e.creation}")
        print(f"METHOD: {e.method}")
        print(e.error)
        print("="*50)

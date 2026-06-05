import frappe

def run():
    errors = frappe.get_all("Error Log", 
        fields=["name", "error", "creation"], 
        order_by="creation desc", limit=5)
    
    for e in errors:
        print("="*80)
        print(f"ERROR NAME: {e.name}")
        print(f"CREATED AT: {e.creation}")
        print("-" * 40)
        print(e.error)
        print("="*80)
        print("\n")

if __name__ == "__main__":
    run()

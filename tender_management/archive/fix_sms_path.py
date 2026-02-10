import frappe

def run():
    print("--- 🛣️ FIXING PYTHON PATH IN CLIENT SCRIPT ---")

    # The CORRECT Python path (one 'tender_management')
    correct_method = "tender_management.sms_handler.send_sms"

    # List of scripts to update
    scripts = frappe.db.sql("""
        SELECT name, script 
        FROM `tabClient Script` 
        WHERE script LIKE '%tender_management.tender_management.sms_handler%'
    """, as_dict=True)

    count = 0
    for s in scripts:
        # Replace the bad path with the good one
        new_code = s.script.replace(
            "tender_management.tender_management.sms_handler.send_sms", 
            correct_method
        )
        
        frappe.db.set_value("Client Script", s.name, "script", new_code)
        count += 1
        print(f"  ✔ Fixed path in script: {s.name}")

    frappe.db.commit()
    print(f"--- ✅ UPDATED {count} SCRIPTS ---")
    
    # Verify the Python file exists where we expect it
    import os
    file_path = "apps/tender_management/tender_management/sms_handler.py"
    if os.path.exists(file_path):
        print("  ✔ Python file exists on server.")
    else:
        print("  ❌ Python file is MISSING! Re-run the file creation script.")

if __name__ == "__main__":
    run()

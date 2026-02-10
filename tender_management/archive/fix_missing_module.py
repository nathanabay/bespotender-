import os
import sys

def run():
    print("--- 🔍 DIAGNOSING MISSING MODULE ERROR ---")

    # 1. VERIFY FILE PATH
    expected_path = "apps/tender_management/tender_management/sms_handler.py"
    
    if os.path.exists(expected_path):
        print(f"✔ File found at: {expected_path}")
        
        # Verify content
        with open(expected_path, 'r') as f:
            content = f.read()
            if "def send_sms" in content and "@frappe.whitelist()" in content:
                print("✔ Content looks correct (contains send_sms and whitelist)")
            else:
                print("⚠ File exists but content might be wrong.")
    else:
        print(f"❌ File NOT found at: {expected_path}")
        print("Re-creating the file now...")
        
        # Re-create the file just in case
        with open(expected_path, "w") as f:
            f.write("""import frappe
import requests

@frappe.whitelist()
def send_sms(msisdn, text):
    try:
        api_key = "3IFW2DBFG9NKIYBVUOR6JXWR88BVE1FK"
        url = "https://smsethiopia.et/api/send"
        
        headers = {"KEY": api_key, "Content-Type": "application/json"}
        payload = {"msisdn": msisdn, "text": text}

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        frappe.log_error(f"SMS Error: {str(e)}")
        return {"status": "error", "message": str(e)}
""")
        print("✔ File re-created successfully.")

    # 2. CHECK INIT FILE
    # Python needs __init__.py to treat directories as packages
    init_path = "apps/tender_management/tender_management/__init__.py"
    if not os.path.exists(init_path):
        print("⚠ Missing __init__.py! Creating it...")
        with open(init_path, "w") as f:
            f.write("")
        print("✔ Created __init__.py")
    else:
        print("✔ __init__.py exists.")

    print("--- ✅ MODULE FIX COMPLETE ---")
    print("👉 ACTION REQUIRED: Run 'bench restart' immediately after this.")

if __name__ == "__main__":
    run()

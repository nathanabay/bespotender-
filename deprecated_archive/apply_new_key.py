import frappe

def run():
    print("--- 🔑 APPLYING NEW SMS API KEY ---")
    
    # 1. DEFINE NEW CONFIG
    NEW_KEY = "VZRZD8VLZW1702V84HOVY0FBDO9BWRDD"
    CORRECT_URL = "https://smsethiopia.et/api/sms/send"
    
    # 2. GENERATE PYTHON FILE CONTENT
    # We use the 'smart' logic: try official URL, fallback to scanner URL
    new_content = f"""import frappe
import requests

@frappe.whitelist()
def send_sms(msisdn, text):
    try:
        api_key = "{NEW_KEY}"
        
        # Headers
        headers = {{
            "KEY": api_key,
            "Content-Type": "application/json"
        }}
        
        # Payload
        payload = {{
            "msisdn": msisdn,
            "text": text
        }}

        # 1. Try Scanner-Found URL (Most likely to work)
        url = "{CORRECT_URL}"
        
        frappe.log_error(title="SMS Debug", message=f"Sending to {{url}} with key {{api_key[:5]}}...")
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
            
        # 2. Fallback: Try Official URL if first fails
        elif response.status_code == 404:
            url_backup = "https://smsethiopia.et/api/send"
            response = requests.post(url_backup, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()

        # Log failure
        return {{"status": "error", "message": f"HTTP {{response.status_code}}: {{response.text}}"}}
            
    except Exception as e:
        frappe.log_error(title="SMS Exception", message=str(e))
        return {{"status": "error", "message": str(e)}}
"""

    # 3. WRITE TO FILE
    file_path = "apps/tender_management/tender_management/sms_handler.py"
    with open(file_path, "w") as f:
        f.write(new_content)
        
    print(f"✔ Key updated to: {NEW_KEY}")
    print("✔ URL set to: " + CORRECT_URL)

if __name__ == "__main__":
    run()

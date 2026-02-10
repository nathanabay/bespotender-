import frappe
import requests

@frappe.whitelist()
def send_sms(msisdn, text):
    try:
        # ✅ YOUR NEW KEY
        api_key = "VZRZD8VLZW1702V84HOVY0FBDO9BWRDD"
        
        # Headers
        headers = {
            "KEY": api_key,
            "Content-Type": "application/json"
        }
        
        # Payload
        payload = {
            "msisdn": msisdn,
            "text": text
        }

        # 1. Try Scanner-Found URL (Primary)
        url = "https://smsethiopia.et/api/sms/send"
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
            
        # 2. Fallback: Try Official URL if first fails with 404
        elif response.status_code == 404:
            url_backup = "https://smsethiopia.et/api/send"
            response = requests.post(url_backup, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()

        # Return failure message
        return {"status": "error", "message": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        frappe.log_error(title="SMS Exception", message=str(e))
        return {"status": "error", "message": str(e)}

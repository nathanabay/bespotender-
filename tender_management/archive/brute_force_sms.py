import requests
import frappe

def run():
    print("--- 🔓 BRUTE FORCING SMS AUTHENTICATION ---")

    # YOUR NEW KEY
    api_key = "VZRZD8VLZW1702V84HOVY0FBDO9BWRDD"
    url = "https://smsethiopia.et/api/sms/send"
    
    # Payload
    payload_base = {"msisdn": "0911000000", "text": "ping"}

    # We will try all these combinations (Name, Headers, BodyExtra, URLParams)
    strategies = [
        # Strategy 1: Headers (Standard)
        ("Header: KEY", {"KEY": api_key}, {}, {}),
        ("Header: Authorization (Bearer)", {"Authorization": f"Bearer {api_key}"}, {}, {}),
        ("Header: Authorization (Raw)", {"Authorization": api_key}, {}, {}),
        ("Header: X-API-KEY", {"X-API-KEY": api_key}, {}, {}),
        ("Header: api-key", {"api-key": api_key}, {}, {}),
        
        # Strategy 2: Body Parameters (Hidden in data)
        ("Body: key", {}, {"key": api_key}, {}),
        ("Body: api_key", {}, {"api_key": api_key}, {}),
        ("Body: token", {}, {"token": api_key}, {}),
        
        # Strategy 3: Query Parameters (In URL)
        ("URL: key", {}, {}, {"key": api_key}),
        ("URL: api_key", {}, {}, {"api_key": api_key}),
    ]

    found_strategy = None

    for name, headers, body_extra, params in strategies:
        print(f"Testing {name} ...", end=" ")
        
        # Merge payload
        payload = payload_base.copy()
        payload.update(body_extra)
        
        # Merge headers
        req_headers = {"Content-Type": "application/json"}
        req_headers.update(headers)

        try:
            r = requests.post(url, json=payload, headers=req_headers, params=params, timeout=5)
            
            # If we get ANY status other than 401/403, it means Auth worked!
            if r.status_code == 200:
                print(f"✅ SUCCESS! [{r.status_code}]")
                found_strategy = (headers, body_extra, params)
                break
            elif r.status_code == 400: 
                print(f"✅ AUTH ACCEPTED (Bad Request) [{r.status_code}]")
                found_strategy = (headers, body_extra, params)
                break
            elif r.status_code == 401:
                print(f"❌ Failed (Unauthorized)")
            else:
                print(f"⚠ [{r.status_code}] {r.text[:50]}")
                
        except Exception as e:
            print(f"❌ Connection Error")

    if found_strategy:
        print("\n👉 UPDATING HANDLER WITH WORKING STRATEGY...")
        update_handler(found_strategy)
    else:
        print("\n❌ ALL STRATEGIES FAILED.")
        print("👉 CONCLUSION: Your API Key is likely inactive or requires admin approval.")
        print("👉 ACTION: Please contact SMSEthiopia support (0976455555) and ask them to activate your API Key.")

def update_handler(strategy):
    headers, body_extra, params = strategy
    
    file_path = "apps/tender_management/tender_management/sms_handler.py"
    
    # Generate cleaner code
    new_code = f"""import frappe
import requests

@frappe.whitelist()
def send_sms(msisdn, text):
    try:
        api_key = "VZRZD8VLZW1702V84HOVY0FBDO9BWRDD"
        url = "https://smsethiopia.et/api/sms/send"
        
        # DYNAMIC HEADERS
        headers = {headers}
        headers["Content-Type"] = "application/json"
        
        # DYNAMIC PAYLOAD
        payload = {{
            "msisdn": msisdn,
            "text": text
        }}
        payload.update({body_extra})
        
        # DYNAMIC PARAMS
        params = {params}
        
        # Send
        response = requests.post(url, json=payload, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {{"status": "error", "message": f"HTTP {{response.status_code}}: {{response.text}}"}}
            
    except Exception as e:
        frappe.log_error(title="SMS Error", message=str(e))
        return {{"status": "error", "message": str(e)}}
"""
    with open(file_path, "w") as f:
        f.write(new_code)
    
    print("✔ sms_handler.py updated.")

if __name__ == "__main__":
    run()

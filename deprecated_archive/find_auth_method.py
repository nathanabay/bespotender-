import requests
import frappe

def run():
    print("--- 🔐 TESTING AUTHENTICATION METHODS ---")

    api_key = "3IFW2DBFG9NKIYBVUOR6JXWR88BVE1FK"
    url = "https://smsethiopia.et/api/sms/send"
    
    # We will test all these different ways to send the key
    tests = [
        ("Header: KEY", {"KEY": api_key}, {}),
        ("Header: Authorization (Bearer)", {"Authorization": f"Bearer {api_key}"}, {}),
        ("Header: Authorization (Raw)", {"Authorization": api_key}, {}),
        ("Header: api-key", {"api-key": api_key}, {}),
        ("Body: key", {}, {"key": api_key}),
        ("Body: api_key", {}, {"api_key": api_key}),
        ("Query Param", {}, {}, {"key": api_key}) # Query param test
    ]
    
    payload_base = {"msisdn": "0911000000", "text": "ping"}

    found_method = None

    for name, headers, body_extra, *params in tests:
        print(f"Testing {name} ...", end=" ")
        
        # Merge body
        payload = payload_base.copy()
        payload.update(body_extra)
        
        # Merge headers
        req_headers = {"Content-Type": "application/json"}
        req_headers.update(headers)

        try:
            r = requests.post(url, json=payload, headers=req_headers, timeout=5)
            
            # If we get anything other than 401, it worked!
            if r.status_code == 200:
                print(f"✅ SUCCESS! [{r.status_code}]")
                found_method = (headers, body_extra)
                break
            elif r.status_code == 400: # 400 means "Bad Request" (missing field?), but AUTH worked!
                print(f"✅ AUTH ACCEPTED (Data Error) [{r.status_code}]")
                found_method = (headers, body_extra)
                break
            else:
                print(f"❌ Failed [{r.status_code}]")
                
        except Exception as e:
            print(f"❌ Connection Error")

    if found_method:
        print("\n👉 UPDATING HANDLER WITH WORKING METHOD...")
        update_handler(found_method)
    else:
        print("\n❌ ALL AUTH METHODS FAILED. PLEASE CHECK IF KEY IS EXPIRED OR INVALID.")

def update_handler(method_data):
    headers, body_extra = method_data
    
    # Generate the new Python code dynamically
    header_str = str(headers).replace("'", '"')
    
    file_path = "apps/tender_management/tender_management/sms_handler.py"
    
    new_code = f"""import frappe
import requests

@frappe.whitelist()
def send_sms(msisdn, text):
    try:
        api_key = "3IFW2DBFG9NKIYBVUOR6JXWR88BVE1FK"
        url = "https://smsethiopia.et/api/sms/send"
        
        # ✅ DYNAMICALLY FOUND HEADERS
        headers = {header_str}
        headers["Content-Type"] = "application/json"
        
        payload = {{
            "msisdn": msisdn,
            "text": text
        }}
        
        # Send
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
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

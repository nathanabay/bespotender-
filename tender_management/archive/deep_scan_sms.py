import requests
import frappe

def run():
    print("--- 📡 DEEP SCANNING FOR SMS API ENDPOINT ---")

    # Your Key
    api_key = "3IFW2DBFG9NKIYBVUOR6JXWR88BVE1FK"
    
    # Common variations for SMS Gateways
    paths = [
        "/api/send",
        "/api/v1/send",
        "/api/v2/send",
        "/api/sms/send",
        "/sms/send",
        "/sms/api/send",
        "/v1/send",
        "/send",
        "/sendsms",
        "/api/sendsms",
        "/messages",
        "/api/messages"
    ]
    
    domains = [
        "https://smsethiopia.et",
        "https://api.smsethiopia.et",
        "https://app.smsethiopia.et"
    ]

    found_url = None
    
    headers = {"KEY": api_key, "Content-Type": "application/json"}
    payload = {"msisdn": "0911000000", "text": "ping"}

    print(f"Scanning {len(domains) * len(paths)} combinations...")

    for domain in domains:
        for path in paths:
            url = f"{domain}{path}"
            # print(f"Trying: {url} ...", end=" ")
            
            try:
                # Test POST
                r = requests.post(url, json=payload, headers=headers, timeout=3)
                
                # If status is NOT 404, we found a listener!
                if r.status_code != 404:
                    print(f"\n✅ FOUND MATCH! URL: {url}")
                    print(f"   Status: {r.status_code}")
                    print(f"   Response: {r.text[:100]}...") # Show first 100 chars
                    found_url = url
                    break
            except:
                pass # Ignore connection errors
        
        if found_url: break

    if found_url:
        print(f"\n👉 UPDATING SYSTEM TO USE: {found_url}")
        update_handler(found_url)
    else:
        print("\n❌ SCAN FAILED. Please log in to smsethiopia.et and copy the 'Endpoint URL'.")

def update_handler(new_url):
    file_path = "apps/tender_management/tender_management/sms_handler.py"
    with open(file_path, "r") as f:
        content = f.read()
    
    import re
    # Regex to find the url = "..." line and replace it
    new_content = re.sub(r'url = ".*?"', f'url = "{new_url}"', content)
    
    with open(file_path, "w") as f:
        f.write(new_content)
    
    print("✔ sms_handler.py updated.")

if __name__ == "__main__":
    run()

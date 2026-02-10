import requests
import frappe

def run():
    print("--- 🕵️ LOOKING FOR CORRECT SMS ENDPOINT ---")

    # We will test all these potential addresses
    potential_urls = [
        "https://smsethiopia.et/api/send",       # Current (404)
        "https://smsethiopia.com/api/send",      # .com version
        "https://api.smsethiopia.et/send",       # Subdomain
        "https://api.smsethiopia.com/send",      # .com Subdomain
        "https://smsethiopia.et/api/v1/send",    # Versioned
        "https://sms.ethio.et/api/send",         # Common alternative
    ]

    api_key = "3IFW2DBFG9NKIYBVUOR6JXWR88BVE1FK"
    
    # We send a dummy request. We WANT a 400 (Bad Request) or 401 (Auth).
    # If we get 404, the URL is wrong.
    headers = {"KEY": api_key, "Content-Type": "application/json"}
    payload = {"msisdn": "0900000000", "text": "ping"}

    found_url = None

    for url in potential_urls:
        print(f"Testing: {url} ...", end=" ")
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=5)
            print(f"[{r.status_code}]")
            
            # 200 = Success (Found!)
            # 400/401/403 = Endpoint exists, but maybe key/data invalid (Found!)
            # 404 = Wrong Address (Keep looking)
            # 405 = Wrong Method (Maybe it's GET?)
            
            if r.status_code != 404:
                print(f"✅ FOUND IT! The server responded at: {url}")
                found_url = url
                break
                
        except Exception as e:
            print("❌ Connection Error")

    if found_url:
        print(f"\n👉 UPDATING SYSTEM TO USE: {found_url}")
        update_handler(found_url)
    else:
        print("\n❌ Could not find a working endpoint. Please check the API documentation.")

def update_handler(new_url):
    # Overwrite the handler file with the correct URL
    file_path = "apps/tender_management/tender_management/sms_handler.py"
    with open(file_path, "r") as f:
        content = f.read()
    
    # Replace the old URL with the new one
    import re
    new_content = re.sub(r'url = ".*?"', f'url = "{new_url}"', content)
    
    with open(file_path, "w") as f:
        f.write(new_content)
    
    print("✔ sms_handler.py updated.")
    print("⚠ PLEASE RUN 'bench restart' TO APPLY CHANGES.")

if __name__ == "__main__":
    run()

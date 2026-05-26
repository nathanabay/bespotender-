import frappe

def run():
    print("--- 🔑 APPLYING SMS API KEY ---")

    API_KEY = "3IFW2DBFG9NKIYBVUOR6JXWR88BVE1FK"

    # 1. UPDATE SMS SETTINGS (Standard Module)
    # This enables the native ERPNext SMS feature
    sms_settings = frappe.get_doc("SMS Settings")
    sms_settings.sms_gateway_url = "https://smsethiopia.et/api/send"
    sms_settings.message_parameter = "text"
    sms_settings.receiver_parameter = "msisdn"
    sms_settings.use_post = 1
    
    # Rebuild headers with the real key
    sms_settings.headers = []
    sms_settings.append("headers", {
        "header": "KEY",
        "value": API_KEY
    })
    sms_settings.append("headers", {
        "header": "Content-Type",
        "value": "application/json"
    })
    
    sms_settings.save()
    print("✔ Standard SMS Settings Updated")

    # 2. UPDATE CUSTOM BUTTON SCRIPT
    # This updates the "Send SMS (Ethiopia)" button to skip the key prompt
    script_name = "SMSEthiopia Integration"
    
    js_code = f"""
frappe.ui.form.on(['Sales Invoice', 'Tender Opportunity'], {{
    refresh: function(frm) {{
        if (!frm.is_new()) {{
            frm.add_custom_button(__('Send SMS (Ethiopia)'), function() {{
                
                // 1. Identify Mobile Number
                let mobile = frm.doc.contact_mobile || frm.doc.mobile_no || frm.doc.phone || "";
                
                // 2. Simple Prompt (Only Message needed now)
                frappe.prompt([
                    {{
                        label: 'Mobile Number',
                        fieldname: 'msisdn',
                        fieldtype: 'Data',
                        default: mobile,
                        reqd: 1
                    }},
                    {{
                        label: 'Message',
                        fieldname: 'text',
                        fieldtype: 'Small Text',
                        reqd: 1,
                        default: `Hello from Bespo regarding ${{frm.doc.name}}`
                    }}
                ], (values) => {{
                    
                    // 3. Send Request (Key is hardcoded)
                    frappe.call({{
                        method: "frappe.client.post",
                        args: {{
                            "url": "https://smsethiopia.et/api/send",
                            "headers": {{
                                "KEY": "{API_KEY}",
                                "Content-Type": "application/json"
                            }},
                            "data": {{
                                "msisdn": values.msisdn,
                                "text": values.text
                            }}
                        }},
                        callback: function(r) {{
                            // API usually returns 200 even on error, so we check status
                            if (!r.exc && r.message) {{
                                frappe.msgprint("✔ SMS Sent to " + values.msisdn);
                            }} else {{
                                frappe.msgprint("❌ Error Sending SMS.");
                                console.log(r);
                            }}
                        }}
                    }});
                    
                }}, "Send SMS", "Send Now");
                
            }}, "Actions");
        }}
    }}
}});
    """

    if frappe.db.exists("Client Script", script_name):
        doc = frappe.get_doc("Client Script", script_name)
        doc.script = js_code
        doc.save(ignore_permissions=True)
        print("✔ Custom 'Send SMS' Button Updated with Key")

    print("--- ✅ KEY SAVED ---")

if __name__ == "__main__":
    run()

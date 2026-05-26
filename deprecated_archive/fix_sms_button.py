import frappe

def run():
    print("--- 🔑 HARDCODING API KEY INTO SMS BUTTON ---")

    API_KEY = "3IFW2DBFG9NKIYBVUOR6JXWR88BVE1FK"

    # Define the Client Script with the Key embedded
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
                    
                    // 3. Send Request (Key is hardcoded here)
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
                            if (!r.exc) {{
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

    # Update or Create the Client Script
    if frappe.db.exists("Client Script", script_name):
        doc = frappe.get_doc("Client Script", script_name)
        doc.script = js_code
        doc.save(ignore_permissions=True)
        print("✔ Client Script updated with API Key")
    else:
        new_doc = frappe.new_doc("Client Script")
        new_doc.name = script_name
        new_doc.dt = "Sales Invoice" # Default, applies to both via code
        new_doc.view = "Form"
        new_doc.script = js_code
        new_doc.enabled = 1
        new_doc.save(ignore_permissions=True)
        print("✔ Client Script created with API Key")

    print("--- ✅ SUCCESS ---")

if __name__ == "__main__":
    run()

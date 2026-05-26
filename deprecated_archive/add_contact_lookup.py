import frappe

def run():
    print("--- 📞 ADDING CONTACT LOOKUP TO SMS BUTTON ---")

    API_KEY = "3IFW2DBFG9NKIYBVUOR6JXWR88BVE1FK"

    script_name = "SMSEthiopia Integration"
    
    js_code = f"""
frappe.ui.form.on(['Sales Invoice', 'Tender Opportunity'], {{
    refresh: function(frm) {{
        if (!frm.is_new()) {{
            frm.add_custom_button(__('Send SMS (Ethiopia)'), function() {{
                
                // 1. Try to find a default number on the form
                let default_mobile = frm.doc.contact_mobile || frm.doc.mobile_no || frm.doc.phone || "";
                
                let d = new frappe.ui.Dialog({{
                    title: 'Send SMS',
                    fields: [
                        {{
                            label: 'Select Contact (Optional)',
                            fieldname: 'contact_link',
                            fieldtype: 'Link',
                            options: 'Contact',
                            description: 'Pick a contact to auto-fill the number.',
                            onchange: function() {{
                                // Fetch mobile number when contact is selected
                                let contact_name = d.get_value('contact_link');
                                if (contact_name) {{
                                    frappe.db.get_value('Contact', contact_name, 'mobile_no')
                                    .then(r => {{
                                        if (r && r.message && r.message.mobile_no) {{
                                            d.set_value('msisdn', r.message.mobile_no);
                                        }} else {{
                                            frappe.msgprint('No mobile number found for this contact.');
                                        }}
                                    }});
                                }}
                            }}
                        }},
                        {{
                            label: 'Mobile Number',
                            fieldname: 'msisdn',
                            fieldtype: 'Data',
                            default: default_mobile,
                            reqd: 1,
                            description: 'Enter manually or auto-filled from contact.'
                        }},
                        {{
                            label: 'Message',
                            fieldname: 'text',
                            fieldtype: 'Small Text',
                            reqd: 1,
                            default: `Hello from Bespo regarding ${{frm.doc.name}}`
                        }}
                    ],
                    primary_action_label: 'Send Now',
                    primary_action: function(values) {{
                        
                        // 3. Send Request
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
                                if (!r.exc && r.message) {{
                                    frappe.msgprint("✔ SMS Sent to " + values.msisdn);
                                    d.hide();
                                }} else {{
                                    frappe.msgprint("❌ Error Sending SMS.");
                                    console.log(r);
                                }}
                            }}
                        }});
                    }}
                }});
                
                d.show();
                
            }}, "Actions");
        }}
    }}
}});
    """

    if frappe.db.exists("Client Script", script_name):
        doc = frappe.get_doc("Client Script", script_name)
        doc.script = js_code
        doc.save(ignore_permissions=True)
        print("✔ Client Script updated with Contact Lookup")

    print("--- ✅ FEATURE ADDED ---")

if __name__ == "__main__":
    run()

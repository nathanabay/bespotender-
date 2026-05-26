import frappe

def run():
    print("--- 🛠️ FIXING GLOBAL SMS SCRIPTS ---")

    API_KEY = "3IFW2DBFG9NKIYBVUOR6JXWR88BVE1FK"

    target_doctypes = [
        "Tender Opportunity",
        "Lead",
        "Customer",
        "Supplier",
        "Contact",
        "Employee",
        "Job Applicant",
        "Quotation",
        "Sales Order",
        "Delivery Note",
        "Sales Invoice",
        "Purchase Order",
        "Purchase Invoice",
        "Project",
        "Task",
        "User"
    ]

    for dt in target_doctypes:
        script_name = f"SMS_Global_{dt.replace(' ', '_')}"
        
        # We explicitly inject the DocType name {dt} into the JS string
        # This prevents the 'cur_frm is undefined' error
        js_code = f"""
frappe.ui.form.on('{dt}', {{
    refresh: function(frm) {{
        if (!frm.is_new()) {{
            frm.add_custom_button(__('Send SMS (Ethiopia)'), function() {{
                
                // A. SMART NUMBER FINDER
                let found_mobile = "";
                let fields_to_check = ['mobile_no', 'contact_mobile', 'phone', 'cell_number', 'contact_phone', 'phone_number'];
                
                for (let field of fields_to_check) {{
                    if (frm.doc[field]) {{
                        found_mobile = frm.doc[field];
                        break;
                    }}
                }}

                // B. THE POPUP DIALOG
                let d = new frappe.ui.Dialog({{
                    title: 'Send SMS (Ethiopia)',
                    fields: [
                        {{
                            label: 'Find Contact (Optional)',
                            fieldname: 'contact_link',
                            fieldtype: 'Link',
                            options: 'Contact',
                            description: 'Select a person to auto-fill the mobile number.',
                            onchange: function() {{
                                let contact_name = d.get_value('contact_link');
                                if (contact_name) {{
                                    frappe.db.get_value('Contact', contact_name, 'mobile_no')
                                    .then(r => {{
                                        if (r && r.message && r.message.mobile_no) {{
                                            d.set_value('msisdn', r.message.mobile_no);
                                        }} else {{
                                            frappe.msgprint('This contact has no mobile number saved.');
                                        }}
                                    }});
                                }}
                            }}
                        }},
                        {{
                            fieldtype: 'Section Break'
                        }},
                        {{
                            label: 'Mobile Number',
                            fieldname: 'msisdn',
                            fieldtype: 'Data',
                            default: found_mobile,
                            reqd: 1,
                            description: 'Enter manually (251...)'
                        }},
                        {{
                            label: 'Message',
                            fieldname: 'text',
                            fieldtype: 'Small Text',
                            reqd: 1,
                            default: `Hello regarding ${{frm.doc.name}}`
                        }}
                    ],
                    primary_action_label: 'Send Now',
                    primary_action: function(values) {{
                        
                        // C. SEND TO API
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
                                    frappe.msgprint("✔ SMS Sent Successfully");
                                    d.hide();
                                }} else {{
                                    frappe.msgprint("❌ SMS Failed.");
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
        
        # Update existing scripts
        if frappe.db.exists("Client Script", script_name):
            doc = frappe.get_doc("Client Script", script_name)
            doc.script = js_code
            doc.save(ignore_permissions=True)
            print(f"  ✔ Fixed: {dt}")
        else:
            print(f"  ℹ Skipped (Not found): {dt}")

    print("--- ✅ ALL SCRIPTS REPAIRED ---")

if __name__ == "__main__":
    run()

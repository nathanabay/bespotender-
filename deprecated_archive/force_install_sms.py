import frappe

def run():
    print("--- 🚀 FORCE INSTALLING GLOBAL SMS (ETHIOPIA) ---")

    API_KEY = "3IFW2DBFG9NKIYBVUOR6JXWR88BVE1FK"

    # List of DocTypes to add the button to
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

    count_created = 0
    count_updated = 0

    for dt in target_doctypes:
        # Check if the DocType actually exists in the system (e.g. ERPNext might not be fully installed)
        if not frappe.db.exists("DocType", dt):
            print(f"  ⚠ Skipping {dt} (DocType not found in system)")
            continue

        script_name = f"SMS_Global_{dt.replace(' ', '_')}"
        
        # The JS Code (Specific to the DocType to avoid errors)
        js_code = f"""
frappe.ui.form.on('{dt}', {{
    refresh: function(frm) {{
        if (!frm.is_new()) {{
            frm.add_custom_button(__('Send SMS (Ethiopia)'), function() {{
                
                // 1. SMART NUMBER FINDER
                let found_mobile = "";
                // List of fields to check for a phone number
                let fields_to_check = ['mobile_no', 'contact_mobile', 'phone', 'cell_number', 'contact_phone', 'phone_number', 'mobile_number'];
                
                for (let field of fields_to_check) {{
                    if (frm.doc[field]) {{
                        found_mobile = frm.doc[field];
                        break;
                    }}
                }}

                // 2. THE POPUP DIALOG
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
                        
                        // 3. SEND TO API
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
                                    frappe.msgprint("❌ SMS Failed. Check number format.");
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

        # CREATE or UPDATE Logic
        if frappe.db.exists("Client Script", script_name):
            doc = frappe.get_doc("Client Script", script_name)
            doc.script = js_code
            doc.save(ignore_permissions=True)
            print(f"  ✔ Updated: {dt}")
            count_updated += 1
        else:
            frappe.get_doc({
                "doctype": "Client Script",
                "dt": dt,
                "view": "Form",
                "name": script_name,
                "script": js_code,
                "enabled": 1
            }).insert(ignore_permissions=True)
            print(f"  ✚ Created: {dt}")
            count_created += 1

    print(f"--- ✅ COMPLETED: {count_created} Created, {count_updated} Updated ---")

if __name__ == "__main__":
    run()

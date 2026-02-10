import frappe

def run():
    print("--- 🧹 CLEANING UP & RE-INSTALLING SMS SCRIPTS ---")

    API_KEY = "3IFW2DBFG9NKIYBVUOR6JXWR88BVE1FK"

    # 1. DELETE OLD SCRIPTS (Avoid conflicts)
    # We delete by name patterns we've used previously to ensure a blank slate
    patterns = ["SMSEthiopia Integration", "SMS_Global_%"]
    
    for pat in patterns:
        frappe.db.sql(f"DELETE FROM `tabClient Script` WHERE name LIKE '{pat}'")
    
    frappe.db.commit()
    print("✔ Deleted old conflicting SMS scripts")

    # 2. DEFINE DOCTYPES
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

    # 3. INSTALL FRESH SCRIPTS
    count = 0
    for dt in target_doctypes:
        if not frappe.db.exists("DocType", dt):
            continue

        script_name = f"SMS_Global_{dt.replace(' ', '_')}"
        
        # JS Code: Wrapped in try-catch to prevent 'Anonymous' crashes
        js_code = f"""
frappe.ui.form.on('{dt}', {{
    refresh: function(frm) {{
        try {{
            if (!frm.is_new()) {{
                // Add Button
                frm.add_custom_button(__('Send SMS (Ethiopia)'), function() {{
                    
                    // 1. SMART FINDER
                    let found_mobile = "";
                    let fields = ['mobile_no', 'contact_mobile', 'phone', 'cell_number', 'contact_phone', 'phone_number'];
                    for (let f of fields) {{
                        if (frm.doc[f]) {{ found_mobile = frm.doc[f]; break; }}
                    }}

                    // 2. DIALOG
                    let d = new frappe.ui.Dialog({{
                        title: 'Send SMS',
                        fields: [
                            {{
                                label: 'Find Contact', fieldname: 'contact_link', fieldtype: 'Link', options: 'Contact',
                                onchange: function() {{
                                    let c = d.get_value('contact_link');
                                    if(c) {{
                                        frappe.db.get_value('Contact', c, 'mobile_no').then(r => {{
                                            if(r && r.message) d.set_value('msisdn', r.message.mobile_no);
                                        }});
                                    }}
                                }}
                            }},
                            {{ fieldtype: 'Section Break' }},
                            {{ label: 'Mobile Number', fieldname: 'msisdn', fieldtype: 'Data', default: found_mobile, reqd: 1 }},
                            {{ label: 'Message', fieldname: 'text', fieldtype: 'Small Text', reqd: 1, default: `Hello regarding ${{frm.doc.name}}` }}
                        ],
                        primary_action_label: 'Send',
                        primary_action: function(v) {{
                            frappe.call({{
                                method: "frappe.client.post",
                                args: {{
                                    "url": "https://smsethiopia.et/api/send",
                                    "headers": {{ "KEY": "{API_KEY}", "Content-Type": "application/json" }},
                                    "data": {{ "msisdn": v.msisdn, "text": v.text }}
                                }},
                                callback: function(r) {{
                                    if(!r.exc) {{ frappe.msgprint("✔ Sent"); d.hide(); }}
                                    else {{ frappe.msgprint("❌ Failed"); console.log(r); }}
                                }}
                            }});
                        }}
                    }});
                    d.show();
                }}, "Actions");
            }}
        }} catch (e) {{
            console.log("SMS Script Error:", e);
        }}
    }}
}});
"""
        # Create new script
        frappe.get_doc({
            "doctype": "Client Script",
            "dt": dt,
            "view": "Form",
            "name": script_name,
            "script": js_code,
            "enabled": 1
        }).insert(ignore_permissions=True)
        count += 1

    print(f"--- ✅ INSTALLED {count} FRESH SCRIPTS ---")

if __name__ == "__main__":
    run()

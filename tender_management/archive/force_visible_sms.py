import frappe

def run():
    print("--- 🔵 INSTALLING HIGH-VISIBILITY SMS BUTTONS ---")

    API_KEY = "3IFW2DBFG9NKIYBVUOR6JXWR88BVE1FK"

    # 1. DELETE OLD CONFUSING SCRIPTS
    frappe.db.sql("DELETE FROM `tabClient Script` WHERE name LIKE '%SMS_Global_%'")
    frappe.db.commit()

    # 2. TARGET DOCTYPES
    target_doctypes = [
        "User", # We add this for testing because everyone can access their own User profile
        "Sales Invoice",
        "Customer",
        "Tender Opportunity",
        "Lead",
        "Supplier",
        "Contact",
        "Employee"
    ]

    count = 0

    for dt in target_doctypes:
        if not frappe.db.exists("DocType", dt):
            continue

        script_name = f"SMS_Global_{dt.replace(' ', '_')}"
        
        # JS CODE: Uses 'page.add_inner_button' (Top Bar) instead of 'add_custom_button' (Actions Menu)
        js_code = f"""
frappe.ui.form.on('{dt}', {{
    refresh: function(frm) {{
        // 1. ADD VISIBLE BUTTON (Top Right)
        // This puts it next to 'Save' / 'Submit'
        frm.page.add_inner_button(__('Send SMS'), function() {{
            
            // 2. DATA GATHERING
            let found_mobile = "";
            let fields = ['mobile_no', 'contact_mobile', 'phone', 'cell_number', 'phone_number'];
            for (let f of fields) {{ if (frm.doc[f]) {{ found_mobile = frm.doc[f]; break; }} }}

            // 3. DIALOG
            let d = new frappe.ui.Dialog({{
                title: 'Send SMS (Ethiopia)',
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
                    {{ label: 'Mobile', fieldname: 'msisdn', fieldtype: 'Data', default: found_mobile, reqd: 1 }},
                    {{ label: 'Message', fieldname: 'text', fieldtype: 'Small Text', reqd: 1, default: `Hello regarding ${{frm.doc.name}}` }}
                ],
                primary_action_label: 'Send Now',
                primary_action: function(v) {{
                    frappe.call({{
                        method: "tender_management.tender_management.sms_handler.send_sms",
                        args: {{ "msisdn": v.msisdn, "text": v.text }},
                        freeze: true,
                        callback: function(r) {{
                            if(r.message && (r.message.status === 'success' || r.message.msg === 'Accepted successfully')) {{ 
                                frappe.msgprint("✔ Sent!"); d.hide(); 
                            }} else {{ 
                                frappe.msgprint("❌ Error: " + JSON.stringify(r.message)); 
                            }}
                        }}
                    }});
                }}
            }});
            d.show();

        }}).addClass('btn-primary'); // Make it blue/prominent
    }}
}});
"""

        # INSTALL
        frappe.get_doc({
            "doctype": "Client Script",
            "dt": dt,
            "view": "Form",
            "name": script_name,
            "script": js_code,
            "enabled": 1
        }).insert(ignore_permissions=True)
        count += 1

    print(f"--- ✅ INSTALLED {count} BUTTONS (LOOK AT THE TOP RIGHT) ---")

if __name__ == "__main__":
    run()

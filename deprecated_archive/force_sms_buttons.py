import frappe

def run():
    print("--- 💥 FORCE REINSTALLING SMS BUTTONS ---")

    API_KEY = "3IFW2DBFG9NKIYBVUOR6JXWR88BVE1FK"
    
    # 1. DELETE ALL OLD SMS SCRIPTS
    # We use SQL to find them all, then delete properly
    old_scripts = frappe.db.sql("""
        SELECT name FROM `tabClient Script` 
        WHERE name LIKE '%SMS_Global_%' 
        OR name LIKE '%SMSEthiopia%'
        OR script LIKE '%smsethiopia%'
    """, as_dict=True)

    for s in old_scripts:
        try:
            frappe.delete_doc("Client Script", s.name, force=1)
            print(f"  🗑️ Deleted old script: {s.name}")
        except Exception:
            pass
    
    frappe.db.commit()

    # 2. LIST TARGET DOCTYPES
    target_doctypes = [
        "Tender Opportunity", "Lead", "Customer", "Supplier", "Contact", 
        "Employee", "Job Applicant", "Quotation", "Sales Order", 
        "Delivery Note", "Sales Invoice", "Purchase Order", 
        "Purchase Invoice", "Project", "Task", "User"
    ]

    # 3. CREATE NEW SCRIPTS
    count = 0
    for dt in target_doctypes:
        # Verify DocType exists
        if not frappe.db.exists("DocType", dt):
            continue

        script_name = f"SMS_Global_{dt.replace(' ', '_')}"
        
        # JS Code with Console Log for Debugging
        js_code = f"""
// SMS Script for {dt}
console.log("✅ SMS Script Loaded for: {dt}");

frappe.ui.form.on('{dt}', {{
    refresh: function(frm) {{
        // Ensure we are not on a 'New' document page
        if (!frm.is_new()) {{
            
            // Add Button to 'Actions' Menu
            frm.add_custom_button(__('Send SMS (Ethiopia)'), function() {{
                
                // 1. Find Mobile Number
                let found_mobile = "";
                let fields = ['mobile_no', 'contact_mobile', 'phone', 'cell_number', 'contact_phone', 'phone_number'];
                for (let f of fields) {{
                    if (frm.doc[f]) {{ found_mobile = frm.doc[f]; break; }}
                }}

                // 2. Show Dialog
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
                        {{ label: 'Mobile Number', fieldname: 'msisdn', fieldtype: 'Data', default: found_mobile, reqd: 1 }},
                        {{ label: 'Message', fieldname: 'text', fieldtype: 'Small Text', reqd: 1, default: `Hello regarding ${{frm.doc.name}}` }}
                    ],
                    primary_action_label: 'Send',
                    primary_action: function(v) {{
                        frappe.call({{
                            method: "tender_management.tender_management.sms_handler.send_sms",
                            args: {{ "msisdn": v.msisdn, "text": v.text }},
                            freeze: true,
                            freeze_message: "Sending...",
                            callback: function(r) {{
                                if(r.message && (r.message.status === 'success' || r.message.msg === 'Accepted successfully')) {{ 
                                    frappe.msgprint("✔ SMS Sent"); 
                                    d.hide(); 
                                }} else {{ 
                                    frappe.msgprint("❌ Failed. Check Console."); 
                                    console.log(r); 
                                }}
                            }}
                        }});
                    }}
                }});
                d.show();

            }}, "Actions"); // <--- Explicitly putting it in 'Actions' group
        }}
    }}
}});
"""
        
        # Create Record
        new_doc = frappe.get_doc({
            "doctype": "Client Script",
            "dt": dt,
            "view": "Form",
            "name": script_name,
            "script": js_code,
            "enabled": 1
        })
        new_doc.insert(ignore_permissions=True)
        count += 1

    frappe.db.commit()
    print(f"--- ✅ {count} SCRIPTS RE-CREATED & ENABLED ---")
    print("👉 ACTION REQUIRED: Clear Browser Cache (Ctrl+Shift+R)")

if __name__ == "__main__":
    run()

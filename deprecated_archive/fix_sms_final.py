import frappe

def run():
    print("--- 🔌 CONNECTING SMS BUTTON TO BACKEND HANDLER ---")

    # The new Python method path
    method_path = "tender_management.tender_management.sms_handler.send_sms"

    target_doctypes = [
        "Tender Opportunity", "Lead", "Customer", "Supplier", "Contact", 
        "Employee", "Job Applicant", "Quotation", "Sales Order", 
        "Delivery Note", "Sales Invoice", "Purchase Order", 
        "Purchase Invoice", "Project", "Task", "User"
    ]

    for dt in target_doctypes:
        if not frappe.db.exists("DocType", dt):
            continue

        script_name = f"SMS_Global_{dt.replace(' ', '_')}"
        
        # JS Code: Now calls our custom backend method
        js_code = f"""
frappe.ui.form.on('{dt}', {{
    refresh: function(frm) {{
        // Safe check
        if (!frm || frm.doc.doctype !== '{dt}') return;

        if (!frm.is_new()) {{
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
                        // CALL CUSTOM SERVER METHOD
                        frappe.call({{
                            method: "{method_path}",
                            args: {{ "msisdn": v.msisdn, "text": v.text }},
                            freeze: true,
                            freeze_message: "Sending SMS...",
                            callback: function(r) {{
                                if(r.message && (r.message.status === 'success' || r.message.msg === 'Accepted successfully')) {{ 
                                    frappe.msgprint("✔ SMS Sent Successfully"); 
                                    d.hide(); 
                                }}
                                else {{ 
                                    frappe.msgprint("❌ SMS Failed (Check Error Log)"); 
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
        # Overwrite script
        if frappe.db.exists("Client Script", script_name):
            doc = frappe.get_doc("Client Script", script_name)
            doc.script = js_code
            doc.save(ignore_permissions=True)

    print("--- ✅ SMS BACKEND LINKED ---")

if __name__ == "__main__":
    run()

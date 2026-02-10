import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def run():
    print("--- 💳 INTEGRATING PAYMENT ENTRY WITH TENDERS ---")

    # 1. ADD 'TENDER REFERENCE' TO PAYMENT ENTRY
    # This allows us to track which payment belongs to which tender
    if not frappe.db.has_column("Payment Entry", "custom_tender_ref"):
        create_custom_fields({
            "Payment Entry": [
                {
                    "fieldname": "custom_tender_ref",
                    "label": "Tender Reference",
                    "fieldtype": "Link",
                    "options": "Tender Opportunity",
                    "insert_after": "reference_no",
                    "read_only": 1
                }
            ]
        })
        print("✔ Added 'Tender Reference' to Payment Entry")

    # 2. UPDATE CLIENT SCRIPT TO CREATE PAYMENT
    script_name = "Tender Purchase Logic"
    
    # We are replacing the old logic with the new "Payment Entry" logic
    js_code = """
frappe.ui.form.on('Tender Opportunity', {
    refresh: function(frm) {
        frm.set_df_property('doc_purchase_status', 'read_only', 1);

        let current_user = frappe.session.user;
        let is_manager = frappe.user.has_role('Tender Manager') || frappe.user.has_role('System Manager');
        let is_finance = frappe.user.has_role('Accounts User') || frappe.user.has_role('System Manager');
        let is_purchaser = frm.doc.tender_purchaser === current_user || is_manager;

        // 1. ASSIGN LOGISTICS
        if ((frm.doc.doc_purchase_status == 'Pending Assignment' || !frm.doc.doc_purchase_status) && is_manager) {
            frm.add_custom_button(__('1. Assign Logistics'), function() {
                if(!frm.doc.tender_purchaser) {
                    frappe.msgprint("Please select a <b>Tender Purchaser</b> first.");
                    return;
                }
                frm.set_value('doc_purchase_status', 'Pending Request');
                frm.save_or_update();
            }, "Actions");
        }

        // 2. REQUEST FINANCE
        if (frm.doc.doc_purchase_status == 'Pending Request') {
            if (is_purchaser) {
                frm.add_custom_button(__('2. Request Finance Approval'), function() {
                    if (frm.doc.purchase_price <= 0) {
                        frappe.throw("Please enter the Purchase Price.");
                        return;
                    }
                    frm.set_value('doc_purchase_status', 'Finance Review');
                    frm.save_or_update();
                    frappe.msgprint("Request sent to Finance.");
                }, "Actions");
            }
        }

        // 3. FINANCE: CREATE PAYMENT ENTRY
        if (frm.doc.doc_purchase_status == 'Finance Review' && is_finance) {
            frm.add_custom_button(__('3. Create Payment Entry'), function() {
                
                // 1. Find Employee ID linked to the Purchaser User
                frappe.call({
                    method: "frappe.client.get_value",
                    args: {
                        doctype: "Employee",
                        filters: { user_id: frm.doc.tender_purchaser },
                        fieldname: "name"
                    },
                    callback: function(r) {
                        let employee = r.message ? r.message.name : "";
                        
                        // 2. Open Payment Entry
                        frappe.new_doc('Payment Entry', {
                            "payment_type": "Pay",
                            "party_type": "Employee",
                            "party": employee,
                            "paid_amount": frm.doc.purchase_price,
                            "received_amount": frm.doc.purchase_price,
                            "reference_no": frm.doc.tender_number,
                            "reference_date": frappe.datetime.now_date(),
                            "custom_tender_ref": frm.doc.name,
                            "remarks": "Purchase of Tender Document: " + frm.doc.title
                        });
                        
                        // 3. Update Status (Optimistic)
                        frm.set_value('doc_purchase_status', 'Funds Released');
                        frm.save();
                    }
                });
            }, "Actions");
        }

        // 4. UPLOAD REMINDER
        if (frm.doc.doc_purchase_status == 'Funds Released') {
            frm.dashboard.set_headline_alert("Payment Created. Waiting for <b style='color:red'>Receipt Upload</b>.", "blue");
        }
    },

    validate: function(frm) {
        if (frm.doc.doc_purchase_status == 'Funds Released') {
            if (frm.doc.full_tender_document && frm.doc.payment_receipt_proof) {
                frm.set_value('doc_purchase_status', 'Completed');
                frappe.msgprint("✔ Process Completed!");
            }
        }
    }
});
    """

    # Update script
    if frappe.db.exists("Client Script", script_name):
        doc = frappe.get_doc("Client Script", script_name)
        doc.script = js_code
        doc.save(ignore_permissions=True)
        print("✔ Client Script Logic Updated")

    print("--- ✅ PAYMENT LOGIC DEPLOYED ---")

if __name__ == "__main__":
    run()

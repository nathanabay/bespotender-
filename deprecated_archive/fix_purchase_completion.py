import frappe

def run():
    print("--- 🔧 FIXING PURCHASE COMPLETION LOGIC ---")

    script_name = "Tender Purchase Logic"
    
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
                frappe.call({
                    method: "frappe.client.get_value",
                    args: {
                        doctype: "Employee",
                        filters: { user_id: frm.doc.tender_purchaser },
                        fieldname: "name"
                    },
                    callback: function(r) {
                        let employee = r.message ? r.message.name : "";
                        frappe.new_doc('Payment Entry', {
                            "payment_type": "Pay",
                            "party_type": "Employee",
                            "party": employee,
                            "paid_amount": frm.doc.purchase_price,
                            "received_amount": frm.doc.purchase_price,
                            "reference_no": frm.doc.tender_number,
                            "reference_date": frappe.datetime.now_date(),
                            "custom_tender_ref": frm.doc.name,
                            "remarks": "Purchase of Tender: " + frm.doc.title
                        });
                        
                        // Optimistic update
                        frm.set_value('doc_purchase_status', 'Funds Released');
                        frm.save();
                    }
                });
            }, "Actions");
        }

        // 4. VISUAL CUES
        if (frm.doc.doc_purchase_status == 'Funds Released') {
            frm.dashboard.set_headline_alert("Payment Created. Please upload <b>Receipt</b> & <b>Document</b> and click Save.", "orange");
        } else if (frm.doc.doc_purchase_status == 'Completed') {
            frm.dashboard.set_headline_alert("✔ Purchase Process Completed.", "green");
        }
    },

    // TRIGGER 1: When Receipt is Uploaded
    payment_receipt_proof: function(frm) {
        frm.trigger('check_completion');
    },

    // TRIGGER 2: When Doc is Uploaded
    full_tender_document: function(frm) {
        frm.trigger('check_completion');
    },

    // LOGIC: Check if both are present
    check_completion: function(frm) {
        if (frm.doc.doc_purchase_status == 'Funds Released') {
            if (frm.doc.full_tender_document && frm.doc.payment_receipt_proof) {
                frappe.show_alert({message: "Both files detected. Marking Completed...", indicator: "green"});
                frm.set_value('doc_purchase_status', 'Completed');
                frm.save(); // Auto-save to lock it in
            }
        }
    }
});
    """

    if frappe.db.exists("Client Script", script_name):
        doc = frappe.get_doc("Client Script", script_name)
        doc.script = js_code
        doc.save(ignore_permissions=True)
        print("✔ Client Script Updated: Added Auto-Completion Triggers")

    print("--- ✅ LOGIC FIXED ---")

if __name__ == "__main__":
    run()

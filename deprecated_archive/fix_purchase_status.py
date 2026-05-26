import frappe

def run():
    print("--- 🔧 FIXING PURCHASE STATUS UPDATE ISSUE ---")

    dt = "Tender Opportunity"
    field = "doc_purchase_status"

    # 1. UPDATE DOCTYPE: Make field writable in DB
    if frappe.db.exists("DocField", {"parent": dt, "fieldname": field}):
        # Set read_only to 0 in the database schema
        frappe.db.sql(f"""
            UPDATE `tabDocField` 
            SET read_only = 0 
            WHERE parent = '{dt}' AND fieldname = '{field}'
        """)
        frappe.clear_cache(doctype=dt)
        print("✔ Unlocked 'Purchase Status' field in Schema")

    # 2. UPDATE CLIENT SCRIPT: Lock field in UI only
    script_name = "Tender Purchase Logic"
    
    # We define the JS again, but add the visual lock in the refresh event
    js_code = """
frappe.ui.form.on('Tender Opportunity', {
    refresh: function(frm) {
        // VISUAL LOCK: Prevent manual editing
        frm.set_df_property('doc_purchase_status', 'read_only', 1);

        if (frm.doc.workflow_state === 'Rejected') return;

        // 1. REQUEST FUNDS (User)
        // Check if status is Pending OR empty/null
        if (frm.doc.purchase_price > 0 && (frm.doc.doc_purchase_status == 'Pending' || !frm.doc.doc_purchase_status)) {
            frm.add_custom_button(__('Request Funds'), function() {
                frm.set_value('doc_purchase_status', 'Requested');
                frm.save_or_update(); // Use robust save
                frappe.msgprint("Funds requested. Admin notified.");
            }, "Actions");
        }

        // 2. APPROVE PAYMENT (Admin)
        if (frm.doc.doc_purchase_status == 'Requested' && (frappe.user.has_role('System Manager') || frappe.user.has_role('Tender Manager'))) {
            frm.add_custom_button(__('Approve Payment'), function() {
                frm.set_value('doc_purchase_status', 'Approved');
                frm.save_or_update();
                frappe.show_alert({message: "Payment Approved", indicator: "green"});
            }, "Actions");
        }

        // 3. CONFIRM RELEASE (Admin/Accounts)
        if (frm.doc.doc_purchase_status == 'Approved' && (frappe.user.has_role('System Manager') || frappe.user.has_role('Accounts User'))) {
            frm.add_custom_button(__('Confirm Funds Released'), function() {
                frappe.confirm('Confirm that physical cash/transfer has been made?', () => {
                    frm.set_value('doc_purchase_status', 'Funds Released');
                    frm.save_or_update();
                });
            }, "Actions");
        }
        
        // 4. VISUAL CUE
        if (frm.doc.doc_purchase_status == 'Funds Released') {
            var msg = "💰 Funds released! Please upload the <b style='color:red'>Tender Document</b> and <b style='color:red'>Receipt</b> to complete.";
            frm.dashboard.set_headline_alert(msg, "blue");
        }
    },

    // AUTOMATION: Mark 'Completed'
    validate: function(frm) {
        if (frm.doc.doc_purchase_status == 'Funds Released') {
            if (frm.doc.full_tender_document && frm.doc.payment_receipt_proof) {
                frm.set_value('doc_purchase_status', 'Completed');
                // We don't save here to avoid loops, standard save handles it
            }
        }
    }
});
    """

    if frappe.db.exists("Client Script", script_name):
        doc = frappe.get_doc("Client Script", script_name)
        doc.script = js_code
        doc.save(ignore_permissions=True)
        print("✔ Client Script Updated with Visual Locks")

    print("--- ✅ REPAIR COMPLETE ---")

if __name__ == "__main__":
    run()

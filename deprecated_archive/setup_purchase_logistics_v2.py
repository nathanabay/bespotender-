import frappe

def run():
    print("--- 💸 SETTING UP DOCUMENT PURCHASE LOGISTICS (FIXED) ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. HELPER TO CREATE FIELDS
    def create_field(label, fieldname, fieldtype, options=None):
        df = frappe.new_doc("DocField")
        df.label = label
        df.fieldname = fieldname
        df.fieldtype = fieldtype
        if options: df.options = options
        return df

    # 2. DEFINE THE NEW FIELDS
    f_status = create_field("Purchase Status", "doc_purchase_status", "Select", "Pending\nRequested\nApproved\nFunds Released\nCompleted")
    f_status.default = "Pending"
    f_status.read_only = 1
    f_status.allow_on_submit = 1

    f_doc = create_field("Full Tender Document (PDF)", "full_tender_document", "Attach")
    f_doc.allow_on_submit = 1

    f_receipt = create_field("Purchase Receipt (Scan)", "payment_receipt_proof", "Attach")
    f_receipt.allow_on_submit = 1

    new_fields_map = {
        "doc_purchase_status": f_status,
        "full_tender_document": f_doc,
        "payment_receipt_proof": f_receipt
    }

    # 3. INJECT FIELDS INTO LAYOUT
    final_fields = []
    inserted = False
    existing_names = [f.fieldname for f in doc.fields]
    
    for f in doc.fields:
        final_fields.append(f)
        
        # Insert inside the Purchase section
        if f.fieldname == "purchase_price" and not inserted:
            print("   > Found 'Purchase Price'. Injecting logistics fields...")
            
            for key, nf in new_fields_map.items():
                if key not in existing_names:
                    final_fields.append(nf)
                    print(f"     + Added: {nf.label}")
                else:
                    print(f"     . Skipped (Exists): {nf.label}")
            
            inserted = True

    if inserted:
        doc.fields = final_fields
        doc.save(ignore_permissions=True)
        print("✔ Schema Updated Successfully")
    else:
        print("⚠ Warning: Could not find 'purchase_price' field. Check layout.")

    # 4. INSTALL CLIENT SCRIPT (The Logic)
    script_name = "Tender Purchase Logic"
    if frappe.db.exists("Client Script", script_name):
        frappe.delete_doc("Client Script", script_name)

    js_code = """
frappe.ui.form.on('Tender Opportunity', {
    refresh: function(frm) {
        if (frm.doc.workflow_state === 'Rejected') return;

        // 1. REQUEST FUNDS (User)
        if (frm.doc.purchase_price > 0 && frm.doc.doc_purchase_status == 'Pending' && !frm.doc.__islocal) {
            frm.add_custom_button(__('Request Funds'), function() {
                frm.set_value('doc_purchase_status', 'Requested');
                frm.save();
                frappe.msgprint("Funds requested. Admin notified.");
            }, "Actions");
        }

        // 2. APPROVE PAYMENT (Admin)
        if (frm.doc.doc_purchase_status == 'Requested' && (frappe.user.has_role('System Manager') || frappe.user.has_role('Tender Manager'))) {
            frm.add_custom_button(__('Approve Payment'), function() {
                frm.set_value('doc_purchase_status', 'Approved');
                frm.save();
                frappe.show_alert({message: "Payment Approved", indicator: "green"});
            }, "Actions");
        }

        // 3. CONFIRM RELEASE (Admin/Accounts)
        if (frm.doc.doc_purchase_status == 'Approved' && (frappe.user.has_role('System Manager') || frappe.user.has_role('Accounts User'))) {
            frm.add_custom_button(__('Confirm Funds Released'), function() {
                frappe.confirm('Confirm that physical cash/transfer has been made?', () => {
                    frm.set_value('doc_purchase_status', 'Funds Released');
                    frm.save();
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
                frappe.msgprint("✔ Purchase Cycle Completed!");
            }
        }
    }
});
    """

    frappe.get_doc({
        "doctype": "Client Script",
        "dt": "Tender Opportunity",
        "name": script_name,
        "script": js_code,
        "enabled": 1,
        "view": "Form"
    }).insert(ignore_permissions=True)
    
    print("✔ Client Script Installed")
    print("--- ✅ PURCHASE WORKFLOW DEPLOYED ---")

if __name__ == "__main__":
    run()

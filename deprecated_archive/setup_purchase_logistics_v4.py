import frappe

def run():
    print("--- 🚚 CONFIGURING PURCHASE LOGISTICS & FINANCE WORKFLOW (FIXED) ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. HELPER TO CREATE FIELDS
    def create_field(label, fieldname, fieldtype, options=None, description=None):
        df = frappe.new_doc("DocField")
        df.label = label
        df.fieldname = fieldname
        df.fieldtype = fieldtype
        if options: df.options = options
        if description: df.description = description
        return df

    # 2. CREATE NEW FIELDS
    f_purchaser = create_field("Tender Purchaser", "tender_purchaser", "Link", options="User", description="The employee responsible for buying the document")
    f_purchaser.reqd = 0 # Optional initially

    f_driver = create_field("Assigned Driver", "driver_name", "Data", description="Name of the driver assigned for this trip")

    new_fields_map = {
        "tender_purchaser": f_purchaser,
        "driver_name": f_driver
    }

    # 3. UPDATE STATUS OPTIONS
    status_field = next((f for f in doc.fields if f.fieldname == "doc_purchase_status"), None)
    if status_field:
        status_field.options = "Pending Assignment\nPending Request\nFinance Review\nFunds Released\nCompleted"
        status_field.default = "Pending Assignment"
        print("✔ Updated Status Options")

    # 4. INJECT FIELDS (Logistics Section)
    final_fields = []
    inserted = False
    existing_names = [f.fieldname for f in doc.fields]
    
    for f in doc.fields:
        final_fields.append(f)
        # Add fields right before the purchase price for visibility
        if f.fieldname == "sec_purchase_bond" and not inserted:
            for key, nf in new_fields_map.items():
                if key not in existing_names:
                    final_fields.append(nf)
                    print(f"   + Added Field: {nf.label}")
            inserted = True

    if inserted:
        doc.fields = final_fields
        doc.save(ignore_permissions=True)
        print("✔ Logistics Fields Added")
    else:
        print("⚠ Could not find 'sec_purchase_bond'. Fields not added.")

    # 5. INSTALL ROBUST LOGIC (Client Script)
    script_name = "Tender Purchase Logic"
    
    # Delete old script to ensure clean slate
    if frappe.db.exists("Client Script", script_name):
        frappe.delete_doc("Client Script", script_name)

    js_code = """
frappe.ui.form.on('Tender Opportunity', {
    refresh: function(frm) {
        // LOCK STATUS FIELD
        frm.set_df_property('doc_purchase_status', 'read_only', 1);

        // GET CURRENT USER
        let current_user = frappe.session.user;
        let is_manager = frappe.user.has_role('Tender Manager') || frappe.user.has_role('System Manager');
        let is_finance = frappe.user.has_role('Accounts User') || frappe.user.has_role('System Manager');
        let is_purchaser = frm.doc.tender_purchaser === current_user;

        // STATE 1: PENDING ASSIGNMENT
        // Only Manager can assign logistics
        if ((frm.doc.doc_purchase_status == 'Pending Assignment' || !frm.doc.doc_purchase_status) && is_manager) {
            frm.add_custom_button(__('Assign Logistics'), function() {
                if(!frm.doc.tender_purchaser || !frm.doc.driver_name) {
                    frappe.msgprint("Please select a Tender Purchaser and Driver first.");
                    return;
                }
                frm.set_value('doc_purchase_status', 'Pending Request');
                frm.save_or_update();
                frappe.show_alert({message: "Logistics Assigned", indicator: "green"});
            }, "Actions");
        }

        // STATE 2: PENDING REQUEST
        // Only the Assigned Purchaser can request funds
        if (frm.doc.doc_purchase_status == 'Pending Request') {
            if (is_purchaser || is_manager) {
                frm.add_custom_button(__('Request Finance Approval'), function() {
                    if (frm.doc.purchase_price <= 0) {
                        frappe.msgprint("Please enter the Purchase Price first.");
                        return;
                    }
                    frm.set_value('doc_purchase_status', 'Finance Review');
                    frm.save_or_update();
                    frappe.msgprint("Request sent to Finance.");
                }, "Actions");
            } else {
                frm.dashboard.set_headline_alert("Waiting for " + frm.doc.tender_purchaser + " to request funds.", "orange");
            }
        }

        // STATE 3: FINANCE REVIEW
        // Only Finance can approve
        if (frm.doc.doc_purchase_status == 'Finance Review' && is_finance) {
            frm.add_custom_button(__('Disburse Funds'), function() {
                frappe.confirm(`Release ${frm.doc.purchase_price} to ${frm.doc.tender_purchaser}?`, () => {
                    frm.set_value('doc_purchase_status', 'Funds Released');
                    frm.save_or_update();
                    frappe.show_alert({message: "Funds Released", indicator: "blue"});
                });
            }, "Actions");
        }

        // STATE 4: FUNDS RELEASED
        // Visual Prompt for Upload
        if (frm.doc.doc_purchase_status == 'Funds Released') {
            frm.dashboard.set_headline_alert(`Funds given to ${frm.doc.tender_purchaser}. Waiting for Receipt & Document upload.`, "blue");
        }
    },

    // AUTOMATION: Auto-complete when files are attached
    validate: function(frm) {
        if (frm.doc.doc_purchase_status == 'Funds Released') {
            if (frm.doc.full_tender_document && frm.doc.payment_receipt_proof) {
                frm.set_value('doc_purchase_status', 'Completed');
                frappe.msgprint("✔ Purchase Process Completed Successfully!");
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
    
    print("✔ Logic Updated")
    print("--- ✅ LOGISTICS WORKFLOW LIVE ---")

if __name__ == "__main__":
    run()

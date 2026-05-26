import frappe

def run():
    print("--- 💸 SETTING UP DOCUMENT PURCHASE LOGISTICS ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. ADD NEW FIELDS FOR THE PROCESS
    new_fields = [
        # Status of the money
        frappe.new_doc("DocField", {
            "fieldname": "doc_purchase_status",
            "label": "Purchase Status",
            "fieldtype": "Select",
            "options": "Pending\nRequested\nApproved\nFunds Released\nCompleted",
            "default": "Pending",
            "read_only": 1, # Controlled by buttons only
            "allow_on_submit": 1
        }),
        # The actual big document
        frappe.new_doc("DocField", {
            "fieldname": "full_tender_document",
            "label": "Full Tender Document (PDF)",
            "fieldtype": "Attach",
            "allow_on_submit": 1
        }),
        # The receipt proof
        frappe.new_doc("DocField", {
            "fieldname": "payment_receipt_proof",
            "label": "Purchase Receipt (Scan)",
            "fieldtype": "Attach",
            "allow_on_submit": 1
        })
    ]

    # 2. INJECT FIELDS INTO "Purchase & Bond" SECTION
    final_fields = []
    inserted = False
    
    for f in doc.fields:
        final_fields.append(f)
        
        # Insert inside the Purchase section, right after 'Purchase Price'
        if f.fieldname == "purchase_price" and not inserted:
            for nf in new_fields:
                if not any(x.fieldname == nf.fieldname for x in doc.fields):
                    final_fields.append(nf)
                    print(f"   + Added Field: {nf.label}")
            inserted = True

    if inserted:
        doc.fields = final_fields
        doc.save(ignore_permissions=True)
        print("✔ Schema Updated")
    else:
        print("⚠ Could not find 'purchase_price' field. Please check layout.")

    # 3. CREATE CLIENT SCRIPT FOR BUTTONS & LOGIC
    # This handles the "Admin must approve" interaction
    script_name = "Tender Purchase Logic"
    if frappe.db.exists("Client Script", script_name):
        frappe.delete_doc("Client Script", script_name)

    js_code = """
frappe.ui.form.on('Tender Opportunity', {
    refresh: function(frm) {
        // BUTTON 1: REQUEST FUNDS
        // Visible if Price is set but status is Pending
        if (frm.doc.purchase_price > 0 && frm.doc.doc_purchase_status == 'Pending' && !frm.doc.__islocal) {
            frm.add_custom_button(__('Request Document Funds'), function() {
                frm.set_value('doc_purchase_status', 'Requested');
                frm.save();
                frappe.msgprint("Funds requested. Notify Admin.");
            }, "Actions");
        }

        // BUTTON 2: APPROVE (Admin Only)
        // Visible if Requested
        if (frm.doc.doc_purchase_status == 'Requested' && (frappe.user.has_role('System Manager') || frappe.user.has_role('Tender Manager'))) {
            frm.add_custom_button(__('Approve Payment'), function() {
                frm.set_value('doc_purchase_status', 'Approved');
                frm.save();
                frappe.show_alert({message: "Payment Approved", indicator: "green"});
            }, "Actions");
        }

        // BUTTON 3: RELEASE FUNDS (Admin/Accounts)
        if (frm.doc.doc_purchase_status == 'Approved' && (frappe.user.has_role('System Manager') || frappe.user.has_role('Accounts User'))) {
            frm.add_custom_button(__('Confirm Funds Released'), function() {
                frappe.confirm('Have you physically given the money to the purchaser?', () => {
                    frm.set_value('doc_purchase_status', 'Funds Released');
                    frm.save();
                });
            }, "Actions");
        }
        
        // VISUAL CUES
        if (frm.doc.doc_purchase_status == 'Funds Released') {
            frm.dashboard.set_headline_alert("💰 Funds released! Please upload the Tender Document and Receipt to complete.", "blue");
        }
    },

    // AUTOMATION: Mark 'Completed' when files are uploaded
    validate: function(frm) {
        if (frm.doc.doc_purchase_status == 'Funds Released') {
            if (frm.doc.full_tender_document && frm.doc.payment_receipt_proof) {
                frm.set_value('doc_purchase_status', 'Completed');
                frappe.msgprint("✔ Purchase cycle complete!");
            }
        }
    }
});
    """

    cs = frappe.get_doc({
        "doctype": "Client Script",
        "dt": "Tender Opportunity",
        "name": script_name,
        "script": js_code,
        "enabled": 1,
        "view": "Form"
    })
    cs.insert(ignore_permissions=True)
    print("✔ Client Script Logic Installed")
    print("--- ✅ PURCHASE WORKFLOW DEPLOYED ---")

if __name__ == "__main__":
    run()

import frappe

def run():
    print("--- 🏦 ENHANCING BOND ACCOUNTING (LINK & CREATE) ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. ADD 'LINKED JOURNAL ENTRY' FIELD
    new_field = frappe.new_doc("DocField")
    new_field.fieldname = "cpo_journal_entry"
    new_field.label = "CPO Journal Entry"
    new_field.fieldtype = "Link"
    new_field.options = "Journal Entry"
    new_field.description = "Link the accounting entry that froze these funds."
    new_field.insert_after = "bond_expiry"
    
    final_fields = []
    inserted = False
    
    for f in doc.fields:
        final_fields.append(f)
        if f.fieldname == "bond_expiry" and not inserted:
            if not any(x.fieldname == "cpo_journal_entry" for x in doc.fields):
                final_fields.append(new_field)
                print("   + Added 'CPO Journal Entry' link field")
            inserted = True

    if inserted:
        doc.fields = final_fields
        doc.save(ignore_permissions=True)
        print("✔ Schema Updated")
    else:
        print("⚠ Could not find 'bond_expiry' field.")

    # 2. UPDATE CLIENT SCRIPT (Smart Buttons)
    script_name = "Tender Bond Accounting"
    
    js_code = """
frappe.ui.form.on('Tender Opportunity', {
    refresh: function(frm) {
        let is_finance = frappe.user.has_role('Accounts User') || frappe.user.has_role('System Manager');
        
        // Show buttons only if Bond Amount is set
        if (frm.doc.bond_amount > 0) {
            
            // CASE A: NO JOURNAL LINKED YET
            if (!frm.doc.cpo_journal_entry && is_finance) {
                
                // Button 1: Create New
                frm.add_custom_button(__('Create CPO Journal'), function() {
                    frappe.new_doc('Journal Entry', {
                        "voucher_type": "Bank Entry",
                        "cheque_no": frm.doc.bond_number,
                        "cheque_date": frappe.datetime.now_date(),
                        "bill_date": frm.doc.bond_expiry, // Track expiry in bill date
                        "custom_tender_ref": frm.doc.name,
                        "user_remark": `Issuance of CPO (${frm.doc.bond_validity_days} days) for: ${frm.doc.title}`,
                        "accounts": [
                            {
                                "account": "", // User selects CPO Asset Account
                                "debit_in_account_currency": frm.doc.bond_amount,
                                "description": `CPO #${frm.doc.bond_number} - ${frm.doc.organization}`
                            },
                            {
                                "account": "", // User selects Bank
                                "credit_in_account_currency": frm.doc.bond_amount
                            }
                        ]
                    });
                }, "Actions");
            }
            
            // CASE B: JOURNAL ALREADY LINKED
            else if (frm.doc.cpo_journal_entry) {
                frm.add_custom_button(__('View Accounting Entry'), function() {
                    frappe.set_route('Form', 'Journal Entry', frm.doc.cpo_journal_entry);
                }, "Actions");
                
                frm.dashboard.set_headline_alert(`Funds locked in Journal: <a href='/app/journal-entry/${frm.doc.cpo_journal_entry}'>${frm.doc.cpo_journal_entry}</a>`, "green");
            }
        }
    }
});
    """

    if frappe.db.exists("Client Script", script_name):
        doc = frappe.get_doc("Client Script", script_name)
        doc.script = js_code
        doc.save(ignore_permissions=True)
        print("✔ Client Script Logic Updated")

    print("--- ✅ BOND ACCOUNTING V2 DEPLOYED ---")

if __name__ == "__main__":
    run()

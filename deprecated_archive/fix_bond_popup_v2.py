import frappe

def run():
    print("--- 🔧 FIXING JOURNAL ENTRY POPULATION ---")

    script_name = "Tender Bond Accounting"
    
    js_code = """
frappe.ui.form.on('Tender Opportunity', {
    refresh: function(frm) {
        let is_finance = frappe.user.has_role('Accounts User') || frappe.user.has_role('System Manager');
        
        if (frm.doc.bond_amount > 0) {
            
            // SCENARIO A: CREATE NEW
            if (!frm.doc.cpo_journal_entry && is_finance) {
                
                frm.add_custom_button(__('Create CPO Journal'), function() {
                    
                    frappe.prompt([
                        {
                            label: 'Bank Account (Source)',
                            fieldname: 'bank_account',
                            fieldtype: 'Link',
                            options: 'Account',
                            filters: {'account_type': 'Bank'},
                            reqd: 1 
                        },
                        {
                            label: 'Bank Commission / Fees',
                            fieldname: 'fees',
                            fieldtype: 'Currency',
                            default: 0
                        }
                    ],
                    function(values){
                        let bond_val = flt(frm.doc.bond_amount);
                        let fee_val = flt(values.fees);
                        let total_cr = bond_val + fee_val;
                        
                        let accounts_list = [];

                        // 1. CREDIT BANK (Total Outflow)
                        accounts_list.push({
                            "account": values.bank_account, 
                            "credit_in_account_currency": total_cr,
                            "party_type": "", "party": ""
                        });

                        // 2. DEBIT ASSET (Bond Value)
                        accounts_list.push({
                            "account": "", // User must fill 'Restricted Cash' account manually
                            "debit_in_account_currency": bond_val,
                            "description": "Collateral for CPO #" + frm.doc.bond_number
                        });

                        // 3. DEBIT EXPENSE (Fees)
                        if (fee_val > 0) {
                            accounts_list.push({
                                "account": "", // User must fill 'Bank Charges' account manually
                                "debit_in_account_currency": fee_val,
                                "description": "Bank Commission / Fees"
                            });
                        }

                        // OPEN NEW FORM WITH PRE-FILLED DATA
                        frappe.new_doc('Journal Entry', {
                            "voucher_type": "Bank Entry",
                            "cheque_no": frm.doc.bond_number,
                            "cheque_date": frappe.datetime.now_date(),
                            "bill_date": frm.doc.bond_expiry,
                            "custom_tender_ref": frm.doc.name,
                            "user_remark": "Issuance of Bid Bond for: " + frm.doc.title,
                            "accounts": accounts_list
                        });
                    },
                    'Create Financial Entry',
                    'Draft Journal'
                    );
                }, "Actions");
            }
            
            // SCENARIO B: ALREADY LINKED
            else if (frm.doc.cpo_journal_entry) {
                frm.dashboard.set_headline_alert(`Funds locked in <a href='/app/journal-entry/${frm.doc.cpo_journal_entry}'>${frm.doc.cpo_journal_entry}</a>`, "green");
            }
        }
    }
});
    """

    if frappe.db.exists("Client Script", script_name):
        doc = frappe.get_doc("Client Script", script_name)
        doc.script = js_code
        doc.save(ignore_permissions=True)
        print("✔ Client Script Updated")
    else:
        frappe.get_doc({
            "doctype": "Client Script",
            "dt": "Tender Opportunity",
            "name": script_name,
            "script": js_code,
            "enabled": 1,
            "view": "Form"
        }).insert(ignore_permissions=True)
        print("✔ Client Script Created")

    print("--- ✅ POPULATION LOGIC REPAIRED ---")

if __name__ == "__main__":
    run()

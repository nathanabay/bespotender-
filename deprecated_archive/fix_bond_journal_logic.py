import frappe

def run():
    print("--- 🔧 FIXING JOURNAL ENTRY ACCOUNT POPULATION ---")

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
                            label: 'Bank Account (Source / Credit)',
                            fieldname: 'bank_account',
                            fieldtype: 'Link',
                            options: 'Account',
                            filters: {'account_type': 'Bank'},
                            reqd: 1
                        },
                        {
                            label: 'CPO Asset Account (Destination / Debit)',
                            fieldname: 'asset_account',
                            fieldtype: 'Link',
                            options: 'Account',
                            description: 'Select the Restricted Cash or Security Deposit account.',
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

                        // ROW 1: CREDIT BANK (Total Outflow)
                        accounts_list.push({
                            "account": values.bank_account, 
                            "credit_in_account_currency": total_cr,
                            "debit_in_account_currency": 0,
                            "party_type": "", "party": ""
                        });

                        // ROW 2: DEBIT ASSET (Bond Value)
                        accounts_list.push({
                            "account": values.asset_account,
                            "debit_in_account_currency": bond_val,
                            "credit_in_account_currency": 0,
                            "description": "Collateral for CPO #" + frm.doc.bond_number,
                            "party_type": "", "party": ""
                        });

                        // ROW 3: DEBIT EXPENSE (Fees) - Optional
                        if (fee_val > 0) {
                            accounts_list.push({
                                "account": "", // Leave blank for user to select specific expense account
                                "debit_in_account_currency": fee_val,
                                "credit_in_account_currency": 0,
                                "description": "Bank Commission / Fees"
                            });
                        }

                        // CREATE AND OPEN JOURNAL ENTRY
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
                    'Configure CPO Transaction',
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
        print("✔ Client Script Logic Updated")

    print("--- ✅ JOURNAL ACCOUNTS REPAIRED ---")

if __name__ == "__main__":
    run()

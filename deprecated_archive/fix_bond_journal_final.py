import frappe

def run():
    print("--- 🔧 FIXING JOURNAL ENTRY: ASKING FOR ALL ACCOUNTS ---")

    script_name = "Tender Bond Accounting"
    
    js_code = """
frappe.ui.form.on('Tender Opportunity', {
    refresh: function(frm) {
        let is_finance = frappe.user.has_role('Accounts User') || frappe.user.has_role('System Manager');
        
        if (frm.doc.bond_amount > 0) {
            
            // BUTTON: CREATE NEW
            if (!frm.doc.cpo_journal_entry && is_finance) {
                
                frm.add_custom_button(__('Create CPO Journal'), function() {
                    
                    frappe.prompt([
                        {
                            label: 'Bank Account (Money Out)',
                            fieldname: 'bank_account',
                            fieldtype: 'Link',
                            options: 'Account',
                            filters: {'account_type': 'Bank'},
                            reqd: 1
                        },
                        {
                            label: 'CPO Asset Account (Collateral)',
                            fieldname: 'asset_account',
                            fieldtype: 'Link',
                            options: 'Account',
                            description: 'Account to hold the frozen funds (e.g., Security Deposit / CPO Receivable)',
                            reqd: 1
                        },
                        {
                            label: 'Bank Commission / Fees',
                            fieldname: 'fees',
                            fieldtype: 'Currency',
                            default: 0
                        },
                        {
                            label: 'Expense Account (Bank Charges)',
                            fieldname: 'expense_account',
                            fieldtype: 'Link',
                            options: 'Account',
                            description: 'Required if you entered Fees',
                            depends_on: 'eval:doc.fees > 0'
                        }
                    ],
                    function(values){
                        // VALIDATION: If fees > 0, Expense Account is mandatory
                        if (values.fees > 0 && !values.expense_account) {
                            frappe.msgprint("Please select an Expense Account for the bank fees.");
                            return;
                        }

                        let bond_val = flt(frm.doc.bond_amount);
                        let fee_val = flt(values.fees);
                        let total_cr = bond_val + fee_val;
                        
                        let accounts_list = [];

                        // 1. CREDIT BANK (Total Outflow)
                        accounts_list.push({
                            "account": values.bank_account, 
                            "credit_in_account_currency": total_cr,
                            "debit_in_account_currency": 0,
                            "party_type": "", "party": "",
                            "cost_center": frappe.defaults.get_user_default("Cost Center")
                        });

                        // 2. DEBIT ASSET (Bond Value)
                        accounts_list.push({
                            "account": values.asset_account,
                            "debit_in_account_currency": bond_val,
                            "credit_in_account_currency": 0,
                            "party_type": "", "party": "",
                            "description": "Collateral for CPO #" + frm.doc.bond_number,
                            "cost_center": frappe.defaults.get_user_default("Cost Center")
                        });

                        // 3. DEBIT EXPENSE (Fees) - Only add row if Account is selected
                        if (fee_val > 0 && values.expense_account) {
                            accounts_list.push({
                                "account": values.expense_account,
                                "debit_in_account_currency": fee_val,
                                "credit_in_account_currency": 0,
                                "description": "Bank Commission / Fees",
                                "party_type": "", "party": "",
                                "cost_center": frappe.defaults.get_user_default("Cost Center")
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
            
            // BUTTON: VIEW EXISTING
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

    print("--- ✅ FINAL FIX DEPLOYED ---")

if __name__ == "__main__":
    run()

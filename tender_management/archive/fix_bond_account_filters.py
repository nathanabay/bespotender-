import frappe

def run():
    print("--- 🛡️ FIXING BOND ACCOUNT FILTERS (HIDE GROUPS) ---")

    script_name = "Tender Bond Accounting"
    
    js_code = """
frappe.ui.form.on('Tender Opportunity', {
    refresh: function(frm) {
        let is_finance = frappe.user.has_role('Accounts User') || frappe.user.has_role('System Manager');
        
        if (frm.doc.bond_amount > 0) {
            
            // BUTTON: CREATE NEW
            if (!frm.doc.cpo_journal_entry && is_finance) {
                
                frm.add_custom_button(__('Create CPO Journal'), function() {
                    
                    let d = new frappe.ui.Dialog({
                        title: 'Configure CPO Transaction',
                        fields: [
                            {
                                label: 'Bank Account (Source / Credit)',
                                fieldname: 'bank_account',
                                fieldtype: 'Link',
                                options: 'Account',
                                filters: {
                                    'account_type': 'Bank',
                                    'is_group': 0 // <--- CRITICAL FIX: Only Ledger Accounts
                                },
                                reqd: 1
                            },
                            {
                                label: 'CPO Asset Account (Collateral)',
                                fieldname: 'asset_account',
                                fieldtype: 'Link',
                                options: 'Account',
                                description: 'Account to hold the frozen funds (e.g., Security Deposit / CPO Receivable)',
                                filters: {
                                    'is_group': 0 // <--- CRITICAL FIX
                                },
                                reqd: 1
                            },
                            {
                                fieldtype: 'Section Break',
                                label: 'Commission Calculation'
                            },
                            {
                                label: 'Commission Rate (%)',
                                fieldname: 'commission_rate',
                                fieldtype: 'Float',
                                default: 0.5,
                                onchange: function() {
                                    let rate = d.get_value('commission_rate') || 0;
                                    let bond = frm.doc.bond_amount;
                                    let fee = bond * (rate / 100);
                                    d.set_value('calculated_fee', fee);
                                }
                            },
                            {
                                label: 'Calculated Fee Amount',
                                fieldname: 'calculated_fee',
                                fieldtype: 'Currency',
                                read_only: 1,
                                default: (frm.doc.bond_amount * 0.005)
                            },
                            {
                                label: 'Expense Account (Bank Charges)',
                                fieldname: 'expense_account',
                                fieldtype: 'Link',
                                options: 'Account',
                                description: 'Required if there is a commission fee.',
                                filters: {
                                    'is_group': 0 // <--- CRITICAL FIX
                                }
                            }
                        ],
                        primary_action_label: 'Draft Journal',
                        primary_action: function(values) {
                            
                            // VALIDATION
                            if (values.calculated_fee > 0 && !values.expense_account) {
                                frappe.msgprint("Please select an <b>Expense Account</b> for the calculated fees.");
                                return;
                            }

                            let bond_val = flt(frm.doc.bond_amount);
                            let fee_val = flt(values.calculated_fee);
                            let total_cr = bond_val + fee_val;
                            
                            let accounts_list = [];

                            // 1. CREDIT BANK
                            accounts_list.push({
                                "account": values.bank_account, 
                                "credit_in_account_currency": total_cr,
                                "debit_in_account_currency": 0,
                                "party_type": "", "party": "",
                                "cost_center": frappe.defaults.get_user_default("Cost Center")
                            });

                            // 2. DEBIT ASSET
                            accounts_list.push({
                                "account": values.asset_account,
                                "debit_in_account_currency": bond_val,
                                "credit_in_account_currency": 0,
                                "party_type": "", "party": "",
                                "description": `Collateral for CPO #${frm.doc.bond_number} (${frm.doc.title})`,
                                "cost_center": frappe.defaults.get_user_default("Cost Center")
                            });

                            // 3. DEBIT EXPENSE
                            if (fee_val > 0) {
                                accounts_list.push({
                                    "account": values.expense_account,
                                    "debit_in_account_currency": fee_val,
                                    "credit_in_account_currency": 0,
                                    "description": `Bank Commission (${values.commission_rate}%)`,
                                    "party_type": "", "party": "",
                                    "cost_center": frappe.defaults.get_user_default("Cost Center")
                                });
                            }

                            // CREATE JOURNAL
                            frappe.new_doc('Journal Entry', {
                                "voucher_type": "Bank Entry",
                                "cheque_no": frm.doc.tender_number, 
                                "cheque_date": frappe.datetime.now_date(),
                                "bill_date": frm.doc.bond_expiry,
                                "custom_tender_ref": frm.doc.name,
                                "user_remark": `Issuance of Bid Bond for Tender: ${frm.doc.tender_number}`,
                                "accounts": accounts_list
                            });
                            
                            d.hide();
                        }
                    });
                    
                    d.show();
                    
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

    print("--- ✅ ACCOUNT FILTERS APPLIED ---")

if __name__ == "__main__":
    run()

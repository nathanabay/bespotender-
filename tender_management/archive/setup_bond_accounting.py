import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def run():
    print("--- 🏦 INTEGRATING BID BONDS WITH ACCOUNTING ---")

    # 1. ADD LINK FIELD TO JOURNAL ENTRY
    # This allows us to tag Journal Entries with the Tender ID
    if not frappe.db.has_column("Journal Entry", "custom_tender_ref"):
        create_custom_fields({
            "Journal Entry": [
                {
                    "fieldname": "custom_tender_ref",
                    "label": "Tender Reference",
                    "fieldtype": "Link",
                    "options": "Tender Opportunity",
                    "insert_after": "cheque_date",
                    "read_only": 1
                }
            ]
        })
        print("✔ Added 'Tender Reference' to Journal Entry")

    # 2. CREATE CLIENT SCRIPT FOR BOND LOGIC
    # This adds a "Create Bond Entry" button for Finance users
    script_name = "Tender Bond Accounting"
    if frappe.db.exists("Client Script", script_name):
        frappe.delete_doc("Client Script", script_name)

    js_code = """
frappe.ui.form.on('Tender Opportunity', {
    refresh: function(frm) {
        // Only show if Bond Amount exists and user is Finance/Manager
        let is_finance = frappe.user.has_role('Accounts User') || frappe.user.has_role('System Manager');
        
        if (frm.doc.bond_amount > 0 && is_finance) {
            
            // BUTTON: CREATE CPO ENTRY
            frm.add_custom_button(__('Create CPO Journal'), function() {
                
                // Pre-fill Journal Entry
                frappe.new_doc('Journal Entry', {
                    "voucher_type": "Bank Entry",
                    "cheque_no": frm.doc.bond_number,
                    "cheque_date": frm.doc.bond_expiry,
                    "custom_tender_ref": frm.doc.name,
                    "user_remark": "Issuance of Bid Bond/CPO for Tender: " + frm.doc.title,
                    "accounts": [
                        {
                            "account": "", // User must select CPO Receivable Account
                            "debit_in_account_currency": frm.doc.bond_amount,
                            "party_type": "", 
                            "party": "",
                            "description": "Funds Frozen for CPO: " + frm.doc.tender_number
                        },
                        {
                            "account": "", // User must select Bank Account
                            "credit_in_account_currency": frm.doc.bond_amount,
                            "party_type": "",
                            "party": ""
                        }
                    ]
                });
            }, "Actions");
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

    print("✔ Client Script Logic Installed")
    print("--- ✅ BOND ACCOUNTING DEPLOYED ---")

if __name__ == "__main__":
    run()

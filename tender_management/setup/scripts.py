"""
tender_management/tender_management/setup/scripts.py

Upserts the two Server Scripts that automate Journal Entry and Payment Entry
creation. This is where C-3 (hardcoded BES account names) is fixed: the
scripts now do dynamic account lookups at runtime, log clearly on failure,
and never reference "BES" or a hard-coded account number.
"""
import frappe


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def setup_bid_security_sync():
	"""
	Ensure the legacy 'Auto-Create Bid Security' server script is disabled.
	The new flow uses Bid Security Request with auto-creation from Tender Opportunity.
	"""
	script_name = "Auto-Create Bid Security"
	if frappe.db.exists("Server Script", script_name):
		frappe.db.set_value("Server Script", script_name, "disabled", 1)
		print(f"  ✔ Disabled legacy Server Script: {script_name}")
	else:
		print(f"  ✔ Legacy script not found (nothing to disable): {script_name}")


def setup_bid_security_accounting():
	"""
	Upsert the 'Automate CPO Journal Entry' Server Script.

	C-3 fix: replaced hard-coded 'Earnest Money - BES' and
	'7868687686867 - cbe - BES' with dynamic frappe.db.get_value()
	calls inside the script body. Failures are logged via frappe.log_error
	instead of silently posting to non-existent accounts.
	"""
	script_name = "Automate CPO Journal Entry"

	# This string is the body of the Server Script stored in the database.
	# It runs inside Frappe's sandboxed server-script context where `doc`
	# and `frappe` are already available.
	script_content = """\
# --- Automate CPO Journal Entry ---
# Account names are resolved at runtime; no hardcoded company abbreviations.

company = frappe.db.get_value("Company", {}, "name") or doc.company
if not company:
    frappe.log_error("CPO JE: No company found. Cannot create Journal Entry.", "CPO Automation")

else:
    earnest_money_account = frappe.db.get_value(
        "Account",
        {"account_name": "Earnest Money", "company": company, "is_group": 0},
        "name"
    )
    bank_account = frappe.db.get_value(
        "Account",
        {"account_type": "Bank", "is_group": 0, "company": company, "disabled": 0},
        "name"
    )

    if not earnest_money_account or not bank_account:
        frappe.log_error(
            f"CPO JE: Required accounts not found for company '{company}'. "
            "Ensure an 'Earnest Money' account and at least one active Bank account "
            "exist in the Chart of Accounts.",
            "CPO Automation"
        )

    elif doc.amount > 0 and doc.status == "Active" and not doc.journal_entry:
        # 1. ISSUANCE JOURNAL
        je = frappe.new_doc("Journal Entry")
        je.voucher_type = "Bank Entry"
        je.company = company
        je.posting_date = frappe.utils.nowdate()
        je.cheque_no = doc.cpo_number
        je.cheque_date = frappe.utils.nowdate()
        je.user_remark = f"CPO Issuance for Tender: {doc.tender} (Ref: {doc.cpo_number})"

        je.append("accounts", {
            "account": earnest_money_account,
            "debit_in_account_currency": doc.amount,
            "description": f"CPO Deposit for {doc.tender}"
        })
        je.append("accounts", {
            "account": bank_account,
            "credit_in_account_currency": doc.amount,
            "description": f"CPO Payment for {doc.tender}"
        })

        je.insert(ignore_permissions=True)
        doc.db_set("journal_entry", je.name, update_modified=False)
        frappe.msgprint(f"✔ Journal Entry {je.name} created for CPO")

    elif doc.status == "Released" and doc.journal_entry and not doc.release_journal_entry:
        # 2. REVERSAL JOURNAL
        je = frappe.new_doc("Journal Entry")
        je.voucher_type = "Bank Entry"
        je.company = company
        je.posting_date = frappe.utils.nowdate()
        je.cheque_no = doc.cpo_number
        je.cheque_date = frappe.utils.nowdate()
        je.user_remark = f"CPO Release for Tender: {doc.tender}"

        je.append("accounts", {
            "account": bank_account,
            "debit_in_account_currency": doc.amount,
            "description": f"CPO Release (credit back to Bank) for {doc.tender}"
        })
        je.append("accounts", {
            "account": earnest_money_account,
            "credit_in_account_currency": doc.amount,
            "description": f"CPO Release (clear Earnest Money) for {doc.tender}"
        })

        je.insert(ignore_permissions=True)
        doc.db_set("release_journal_entry", je.name, update_modified=False)
        frappe.msgprint(f"✔ Reversal Journal Entry {je.name} created for CPO Release")
"""

	_upsert_server_script(
		name=script_name,
		script_type="DocType Event",
		reference_doctype="Bid Security",
		doctype_event="After Save",
		script=script_content,
	)


def setup_document_purchase_payment():
	"""
	Upsert the 'Auto Payment Entry - Document Purchase' Server Script.

	C-3 fix: removed hard-coded bank account number and 'BES' fallback.
	Accounts are resolved dynamically; failures are logged clearly.
	"""
	script_name = "Auto Payment Entry - Document Purchase"

	script_content = """\
# --- Automate Document Purchase Payment Entry ---
# Account names are resolved at runtime; no hardcoded company abbreviations.

if doc.doc_purchase_status == "Funds Released" and doc.document_price > 0 and not doc.doc_purchase_payment_entry:
    company = frappe.db.get_value("Company", {}, "name") or doc.company
    if not company:
        frappe.log_error("Doc Purchase PE: No company found.", "Document Purchase Automation")

    else:
        bank_account = frappe.db.get_value(
            "Account",
            {"account_type": "Bank", "is_group": 0, "company": company, "disabled": 0},
            "name"
        )
        expense_account = (
            frappe.db.get_value(
                "Account",
                {"account_name": "Tender Document Purchase", "company": company, "is_group": 0},
                "name"
            )
            or frappe.db.get_value(
                "Account",
                {"company": company, "account_type": "Expense Account", "is_group": 0},
                "name"
            )
        )

        if not bank_account or not expense_account:
            frappe.log_error(
                f"Doc Purchase PE: Required accounts not found for company '{company}'. "
                "Ensure an active Bank account and a 'Tender Document Purchase' expense "
                "account exist in the Chart of Accounts.",
                "Document Purchase Automation"
            )
        else:
            pe = frappe.new_doc("Payment Entry")
            pe.payment_type = "Internal Transfer"
            pe.posting_date = frappe.utils.nowdate()
            pe.company = company
            pe.paid_from = bank_account
            pe.paid_from_account_currency = (
                frappe.db.get_value("Account", bank_account, "account_currency") or "ETB"
            )
            pe.paid_to = expense_account
            pe.paid_to_account_currency = (
                frappe.db.get_value("Account", expense_account, "account_currency") or "ETB"
            )
            pe.paid_amount = doc.document_price
            pe.received_amount = doc.document_price
            pe.reference_no = doc.purchase_receipt_no or doc.name
            pe.reference_date = doc.purchase_date or frappe.utils.nowdate()
            pe.remarks = f"Auto-payment for tender document purchase: {doc.title}"
            pe.flags.ignore_permissions = True
            pe.insert()
            pe.submit()
            doc.db_set("doc_purchase_payment_entry", pe.name, update_modified=False)
            frappe.msgprint(
                f"✔ Payment Entry {pe.name} created for document purchase",
                alert=True, indicator="green"
            )
"""

	_upsert_server_script(
		name=script_name,
		script_type="DocType Event",
		reference_doctype="Tender Opportunity",
		doctype_event="After Save",
		script=script_content,
	)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _upsert_server_script(*, name, script_type, reference_doctype, doctype_event, script):
	if frappe.db.exists("Server Script", name):
		scr = frappe.get_doc("Server Script", name)
		scr.script = script
		scr.save(ignore_permissions=True)
		print(f"  ✔ Updated Server Script: {name}")
	else:
		frappe.get_doc(
			{
				"doctype": "Server Script",
				"name": name,
				"script_type": script_type,
				"reference_doctype": reference_doctype,
				"doctype_event": doctype_event,
				"script": script,
				"disabled": 0,
			}
		).insert(ignore_permissions=True)
		print(f"  ✔ Created Server Script: {name}")

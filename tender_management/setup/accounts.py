"""
tender_management/tender_management/setup/accounts.py

Creates or verifies required Chart-of-Accounts entries for the app.
All 'or "BES"' fallbacks are removed (C-3 / MEDIUM-1 fix): if no company
exists the function bails out with a logged warning rather than silently
posting to a phantom company.
"""
import frappe


def setup_accounts():
	"""Create the 'Tender Document Purchase' expense account."""
	company = frappe.db.get_value("Company", {}, "name")
	if not company:
		frappe.log_error("setup_accounts: No company found. Skipping.", "Tender Management Setup")
		return

	account_name = f"Tender Document Purchase - {company}"

	if frappe.db.exists("Account", account_name):
		print(f"  ✔ Account already exists: {account_name}")
		return

	parent_account = (
		frappe.db.get_value(
			"Account",
			{"company": company, "account_name": "Indirect Expenses", "is_group": 1},
			"name",
		)
		or frappe.db.get_value(
			"Account",
			{"company": company, "root_type": "Expense", "is_group": 1},
			"name",
		)
	)

	if not parent_account:
		print(f"  ⚠ Could not create {account_name}: no suitable parent Expense account found.")
		return

	try:
		frappe.get_doc(
			{
				"doctype": "Account",
				"account_name": "Tender Document Purchase",
				"parent_account": parent_account,
				"is_group": 0,
				"company": company,
				"account_type": "Expense Account",
				"root_type": "Expense",
			}
		).insert(ignore_permissions=True)
		print(f"  ✔ Created Account: {account_name}")
	except Exception as exc:
		print(f"  ⚠ Account {account_name} insert error: {exc}")


def setup_bid_bond_account():
	"""Create the 'Bid Bond Receivable' current-asset account."""
	company = frappe.db.get_value("Company", {}, "name")
	if not company:
		frappe.log_error("setup_bid_bond_account: No company found. Skipping.", "Tender Management Setup")
		return

	account_name = f"Bid Bond Receivable - {company}"

	if frappe.db.exists("Account", account_name):
		print(f"  ✔ Account already exists: {account_name}")
		return

	parent_account = (
		frappe.db.get_value(
			"Account",
			{"company": company, "account_name": "Current Assets", "is_group": 1},
			"name",
		)
		or frappe.db.get_value(
			"Account",
			{"company": company, "root_type": "Asset", "is_group": 1},
			"name",
		)
	)

	if not parent_account:
		print(f"  ⚠ Could not create {account_name}: no suitable parent Asset account found.")
		return

	try:
		frappe.get_doc(
			{
				"doctype": "Account",
				"account_name": "Bid Bond Receivable",
				"parent_account": parent_account,
				"is_group": 0,
				"company": company,
				"account_type": "Receivable",
				"root_type": "Asset",
			}
		).insert(ignore_permissions=True)
		print(f"  ✔ Created Account: {account_name}")
	except Exception as exc:
		print(f"  ⚠ Account {account_name} insert error: {exc}")

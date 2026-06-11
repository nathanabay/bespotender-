"""
tender_management/tender_management/setup/__init__.py

Entry point for all post-install and post-migrate setup logic.
Hooks.py references:
    after_install = "tender_management.tender_management.setup.after_install"
    after_migrate  = "tender_management.tender_management.setup.after_migrate"

Each functional area is split into its own sub-module so that a failure
in one area does not abort setup of every other area.
"""
import frappe


# ---------------------------------------------------------------------------
# Public hooks
# ---------------------------------------------------------------------------

def after_install():
	print("--- Tender Management: after_install ---")

	# Surface the unoconv requirement in the Desk so admins notice it.
	frappe.msgprint(
		msg=(
			"This app requires the <b>unoconv</b> system package for converting "
			"DOCX files to PDF.<br><br>"
			"Run on your server: <code>sudo apt-get install -y unoconv</code><br><br>"
			"Then run: <code>bench restart</code>"
		),
		title="System Dependency Required",
		indicator="orange",
	)

	_run_setup_steps([
		("Module", _setup_module),
		("Default Document Templates", _import(
			"tender_management.setup.templates",
			"create_default_document_templates"
		)),
	])

	print("--- Tender Management: after_install complete ---")


def after_migrate():
	print("--- Tender Management: after_migrate ---")

	from tender_management.setup.accounts import (
		setup_accounts, setup_bid_bond_account,
	)
	from tender_management.setup.charts import (
		setup_dashboard_charts, setup_number_cards,
	)
	from tender_management.setup.workspace import setup_workspace
	from tender_management.setup.workflow import setup_enhanced_workflow
	from tender_management.setup.scripts import (
		setup_bid_security_accounting,
		setup_document_purchase_payment,
	)
	from tender_management.setup.notifications import (
		setup_notifications, setup_user_custom_fields,
	)
	from tender_management.setup.templates import (
		create_default_document_templates,
	)

	_run_setup_steps([
		("Module", _setup_module),
		("Accounts", setup_accounts),
		("Bid Bond Account", setup_bid_bond_account),
		("Dashboard Charts", setup_dashboard_charts),
		("Number Cards", setup_number_cards),
		("Workspace", setup_workspace),
		("Workflow", setup_enhanced_workflow),
		("Bid Security Accounting Script", setup_bid_security_accounting),
		("Document Purchase Payment Script", setup_document_purchase_payment),
		("Notifications", setup_notifications),
		("User Custom Fields", setup_user_custom_fields),
		("Default Document Templates", create_default_document_templates),
	])

	print("--- Tender Management: after_migrate complete ---")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _setup_module():
	if not frappe.db.exists("Module Def", "Tender Management"):
		frappe.get_doc(
			{
				"doctype": "Module Def",
				"module_name": "Tender Management",
				"app_name": "tender_management",
				"title": "Tender Management",
				"package": "tender_management",
			}
		).insert(ignore_permissions=True)
		print("  ✔ Created Module Def: Tender Management")
	else:
		print("  ✔ Module Def already exists: Tender Management")


def _import(module_path, fn_name):
	"""Return a lazy callable that imports and calls fn_name from module_path."""
	def _fn():
		import importlib
		mod = importlib.import_module(module_path)
		return getattr(mod, fn_name)()
	_fn.__name__ = fn_name
	return _fn


def _run_setup_steps(steps):
	"""
	Run each (label, callable) pair.  A failure in one step is logged and
	reported but does not abort the remaining steps.
	"""
	for label, fn in steps:
		try:
			print(f"  → {label}…")
			fn()
		except Exception as exc:
			msg = f"Setup step '{label}' failed: {exc}"
			frappe.log_error(msg, "Tender Management Setup")
			print(f"  ✖ {msg}")


import frappe
import json

def after_install():
    setup_module()
    setup_dashboard_charts()
    setup_number_cards()
    setup_workspace()

def after_migrate():
    setup_module()
    setup_accounts()
    setup_dashboard_charts()
    setup_number_cards()
    setup_workspace()
    setup_enhanced_workflow()
    setup_bid_security_sync()
    setup_bid_security_accounting()
    setup_document_purchase_payment()
    setup_notifications()

def setup_module():
    if not frappe.db.exists("Module Def", "Tender Management"):
        frappe.get_doc({
            "doctype": "Module Def",
            "module_name": "Tender Management",
            "app_name": "tender_management",
            "title": "Tender Management",
            "package": "tender_management"
        }).insert(ignore_permissions=True)

def setup_accounts():
    """
    Create required accounts for tender management automation
    """
    # Get default company
    company = frappe.db.get_value("Company", {}, "name") or "BES"
    
    # Create Tender Document Purchase expense account
    account_name = f"Tender Document Purchase - {company}"
    
    if not frappe.db.exists("Account", account_name):
        # Find parent expense account
        parent_account = frappe.db.get_value("Account", {
            "company": company,
            "account_name": "Indirect Expenses",
            "is_group": 1
        }, "name")
        
        # If no "Indirect Expenses", try "Expenses"
        if not parent_account:
            parent_account = frappe.db.get_value("Account", {
                "company": company,
                "root_type": "Expense",
                "is_group": 1
            }, "name")
        
        if parent_account:
            try:
                frappe.get_doc({
                    "doctype": "Account",
                    "account_name": "Tender Document Purchase",
                    "parent_account": parent_account,
                    "is_group": 0,
                    "company": company,
                    "account_type": "Expense Account",
                    "root_type": "Expense"
                }).insert(ignore_permissions=True)
                print(f"✔ Created Account: {account_name}")
            except frappe.DuplicateEntryError:
                print(f"✔ Account already exists: {account_name}")
        else:
            print(f"⚠ Could not create account {account_name}: No suitable parent account found")
    else:
        print(f"✔ Account already exists: {account_name}")

def setup_dashboard_charts():
    # 1. Pipeline Value Chart
    chart_1 = "Tender Pipeline Value"
    chart_doc = {
        "doctype": "Dashboard Chart",
        "chart_name": chart_1,
        "chart_type": "Group By",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "workflow_state",
        "aggregate_function_based_on": "final_bid_price",
        "aggregate_function": "Sum",
        "type": "Bar",
        "timeseries": 0,
        "is_public": 1,
        "filters_json": "[]",
        "module": "Tender Management"
    }
    
    upsert_dashboard_chart(chart_1, chart_doc)

    # 2. Win Loss Ratio Chart
    chart_2 = "Win Loss Ratio"
    chart_doc_2 = {
        "doctype": "Dashboard Chart",
        "chart_name": chart_2,
        "chart_type": "Count",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "workflow_state",
        "based_on": "creation",
        "timeseries": 0,
        "filters_json": json.dumps([["Tender Opportunity", "workflow_state", "in", ["Approved", "Rejected"]]]),
        "type": "Donut",
        "is_public": 1,
        "module": "Tender Management"
    }
    upsert_dashboard_chart(chart_2, chart_doc_2)

    # 3. Tenders by Sector
    chart_3 = "Tenders by Sector"
    chart_doc_3 = {
        "doctype": "Dashboard Chart",
        "chart_name": chart_3,
        "chart_type": "Group By",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "sector",
        "aggregate_function": "Count",
        "type": "Donut",
        "is_public": 1,
        "filters_json": "[]", # Added mandatory field
        "module": "Tender Management"
    }
    upsert_dashboard_chart(chart_3, chart_doc_3)

    # 4. Monthly Publication Trend
    chart_4 = "Monthly Publication Trend"
    chart_doc_4 = {
        "doctype": "Dashboard Chart",
        "chart_name": chart_4,
        "chart_type": "Sum",
        "document_type": "Tender Opportunity",
        "based_on": "publication_date",
        "timeseries": 1,
        "time_interval": "Monthly",
        "timespan": "Last Year",
        "type": "Line",
        "is_public": 1,
        "filters_json": "[]", # Added mandatory field
        "module": "Tender Management"
    }
    upsert_dashboard_chart(chart_4, chart_doc_4)

    # 5. Bond Type Distribution
    chart_5 = "Bond Type Distribution"
    chart_doc_5 = {
        "doctype": "Dashboard Chart",
        "chart_name": chart_5,
        "chart_type": "Group By",
        "document_type": "Tender Opportunity",
        "group_by_based_on": "bond_type",
        "aggregate_function": "Count",
        "type": "Pie",
        "is_public": 1,
        "filters_json": "[]", # Added mandatory field
        "module": "Tender Management"
    }
    upsert_dashboard_chart(chart_5, chart_doc_5)

def upsert_dashboard_chart(name, doct):
    if not frappe.db.exists("Dashboard Chart", name):
        frappe.get_doc(doct).insert(ignore_permissions=True)
    else:
        doc = frappe.get_doc("Dashboard Chart", name)
        
        # If chart_type or document_type is changing, we must recreate it as they are fixed fields
        recreate = False
        if doct.get("chart_type") and doc.chart_type != doct["chart_type"]:
            recreate = True
        if doct.get("document_type") and doc.document_type != doct["document_type"]:
            recreate = True
            
        if recreate:
            frappe.delete_doc("Dashboard Chart", name, ignore_permissions=True)
            frappe.get_doc(doct).insert(ignore_permissions=True)
            print(f"✔ Recreated Dashboard Chart: {name}")
        else:
            # Avoid setting fixed fields again
            if "chart_type" in doct:
                del doct["chart_type"]
            if "document_type" in doct:
                del doct["document_type"]
                
            doc.update(doct)
            doc.save(ignore_permissions=True)

def setup_number_cards():
    # 1. Total Active Tenders
    card_1 = "Total Active Tenders"
    if not frappe.db.exists("Number Card", card_1):
        frappe.get_doc({
            "doctype": "Number Card",
            "name": card_1,
            "label": "Total Active Tenders",
            "document_type": "Tender Opportunity",
            "function": "Count",
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Month",
            "filters_json": json.dumps([["Tender Opportunity", "status", "!=", "Completed"]]),
            "module": "Tender Management"
        }).insert(ignore_permissions=True)

    # 2. Total Won Value
    card_2 = "Total Won Value"
    if not frappe.db.exists("Number Card", card_2):
        frappe.get_doc({
            "doctype": "Number Card",
            "name": card_2,
            "label": "Total Won Value",
            "document_type": "Tender Opportunity",
            "function": "Sum",
            "aggregate_function_based_on": "final_bid_price",
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Month",
            "filters_json": json.dumps([["Tender Opportunity", "workflow_state", "=", "Won"]]),
            "module": "Tender Management"
        }).insert(ignore_permissions=True)

def setup_workspace():
    workspace_name = "Tender Management"
    
    ws_content = [
        {"type": "header", "data": {"text": "Key Insights", "level": 2}},
        {"type": "card", "data": {"card_name": "Total Active Tenders", "col": 4}},
        {"type": "card", "data": {"card_name": "Total Won Value", "col": 4}},
        {"type": "header", "data": {"text": "Performance & Pipeline", "level": 2}},
        {"type": "chart", "data": {"chart_name": "Tender Pipeline Value", "col": 8}},
        {"type": "chart", "data": {"chart_name": "Win Loss Ratio", "col": 4}},
        {"type": "chart", "data": {"chart_name": "Active Bids per User", "col": 12}},
        {"type": "header", "data": {"text": "Trends & Analysis", "level": 2}},
        {"type": "chart", "data": {"chart_name": "Monthly Publication Trend", "col": 12}},
        {"type": "chart", "data": {"chart_name": "Tenders by Sector", "col": 6}},
        {"type": "chart", "data": {"chart_name": "Bond Type Distribution", "col": 6}},
        {"type": "chart", "data": {"chart_name": "Bid vs No-Bid", "col": 6}},
        {"type": "chart", "data": {"chart_name": "Tenders by Type", "col": 6}},
        {"type": "header", "data": {"text": "Tender Registry", "level": 3}},
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "type": "DocType", "label": "Tenders", "icon": "list", "color": "Grey"}}
    ]

    charts = [
        {"chart_name": "Tender Pipeline Value", "label": "Tender Pipeline Value"},
        {"chart_name": "Win Loss Ratio", "label": "Win Loss Ratio"},
        {"chart_name": "Active Bids per User", "label": "Active Bids per User"},
        {"chart_name": "Monthly Publication Trend", "label": "Monthly Publication Trend"},
        {"chart_name": "Tenders by Sector", "label": "Tenders by Sector"},
        {"chart_name": "Bond Type Distribution", "label": "Bond Type Distribution"},
        {"chart_name": "Bid vs No-Bid", "label": "Bid vs No-Bid"},
        {"chart_name": "Tenders by Type", "label": "Tenders by Type"}
    ]

    number_cards = [
        {"number_card_name": "Total Active Tenders", "label": "Total Active Tenders"},
        {"number_card_name": "Total Won Value", "label": "Total Won Value"}
    ]

    shortcuts = [
        {"link_to": "Tender Opportunity", "type": "DocType", "label": "Tenders", "icon": "list", "color": "Grey"}
    ]

    ws_doc = {
        "doctype": "Workspace",
        "name": workspace_name,
        "label": workspace_name,
        "title": workspace_name,
        "category": "Modules",
        "module": "Tender Management",
        "icon": "folder",
        "public": 1,
        "charts": charts,
        "number_cards": number_cards,
        "shortcuts": shortcuts,
        "content": json.dumps(ws_content),
        "is_hidden": 0
    }

    if not frappe.db.exists("Workspace", workspace_name):
        frappe.get_doc(ws_doc).insert(ignore_permissions=True)
    else:
        doc = frappe.get_doc("Workspace", workspace_name)
        doc.update(ws_doc)
        doc.save(ignore_permissions=True)

def setup_enhanced_workflow():
    wf_name = "Two-Stage Tender Approval"
    if not frappe.db.exists("Workflow", wf_name):
        return

    doc = frappe.get_doc("Workflow", wf_name)
    print(f"🔄 Updating Workflow: {wf_name}")
    
    # 0. Ensure Workflow Actions exist
    required_actions = [
        "Confirm Purchase", "Issue Bond", "Start Technical", 
        "Start Financial", "Finalize", "Submit Bid", 
        "Award Tender", "Regret"
    ]
    for action in required_actions:
        if not frappe.db.exists("Workflow Action Master", action):
            frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(ignore_permissions=True)
            print(f"✔ Created Workflow Action: {action}")

    # States
    new_states = [
        {"state": "Draft", "allow_edit": "Tender User", "doc_status": "0"},
        {"state": "Pending Review", "allow_edit": "Tender Manager", "doc_status": "0"},
        {"state": "Pending Final Approval", "allow_edit": "Tender Director", "doc_status": "0"},
        {"state": "Approved to Bid", "allow_edit": "Tender Manager", "doc_status": "0"},
        {"state": "Tender Purchased", "allow_edit": "Tender Manager", "doc_status": "0"},
        {"state": "Bid Bond Issued", "allow_edit": "Tender Manager", "doc_status": "0"},
        {"state": "Technical Preparation", "allow_edit": "Tender Manager", "doc_status": "0"},
        {"state": "Financial Preparation", "allow_edit": "Tender Manager", "doc_status": "0"},
        {"state": "Ready for Submission", "allow_edit": "Tender Manager", "doc_status": "0"},
        {"state": "Submitted", "allow_edit": "Tender Manager", "doc_status": "1"},
        {"state": "Won", "allow_edit": "Tender Manager", "doc_status": "1"},
        {"state": "Lost", "allow_edit": "Tender Manager", "doc_status": "2"},
        {"state": "Rejected", "allow_edit": "Tender User", "doc_status": "0"}
    ]
    
    doc.set("states", []) 
    for s in new_states:
        doc.append("states", s)
        
    # Transitions
    new_transitions = [
        {"state": "Draft", "action": "Submit for Review", "next_state": "Pending Review", "allowed": "Tender User"},
        {"state": "Pending Review", "action": "Approve (Level 1)", "next_state": "Pending Final Approval", "allowed": "Tender Manager"},
        {"state": "Pending Review", "action": "Reject", "next_state": "Rejected", "allowed": "Tender Manager"},
        {"state": "Pending Final Approval", "action": "Approve (Final)", "next_state": "Approved to Bid", "allowed": "Tender Director"},
        {"state": "Pending Final Approval", "action": "Reject", "next_state": "Rejected", "allowed": "Tender Director"},
        {"state": "Approved to Bid", "action": "Confirm Purchase", "next_state": "Tender Purchased", "allowed": "Tender Manager"},
        {"state": "Tender Purchased", "action": "Issue Bond", "next_state": "Bid Bond Issued", "allowed": "Tender Manager"},
        {"state": "Bid Bond Issued", "action": "Start Technical", "next_state": "Technical Preparation", "allowed": "Tender Manager"},
        {"state": "Technical Preparation", "action": "Start Financial", "next_state": "Financial Preparation", "allowed": "Tender Manager"},
        {"state": "Financial Preparation", "action": "Finalize", "next_state": "Ready for Submission", "allowed": "Tender Manager"},
        {"state": "Ready for Submission", "action": "Submit Bid", "next_state": "Submitted", "allowed": "Tender Manager"},
        {"state": "Submitted", "action": "Award Tender", "next_state": "Won", "allowed": "Tender Director"},
        {"state": "Submitted", "action": "Regret", "next_state": "Lost", "allowed": "Tender Director"},
        {"state": "Rejected", "action": "Restart", "next_state": "Draft", "allowed": "Tender User"}
    ]
    
    doc.set("transitions", []) 
    for t in new_transitions:
        doc.append("transitions", t)
        
    doc.save(ignore_permissions=True)
    print(f"✔ Workflow {wf_name} updated successfully")
    print(f"✔ Workflow {wf_name} updated successfully")

def setup_bid_security_sync():
    script_name = "Auto-Create Bid Security"
    
    script_content = """
# Only run if there is a Bond Amount
if doc.bond_amount and doc.bond_amount > 0:
    # CHECK EXISTING
    existing = frappe.db.get_value("Bid Security", {"tender": doc.name}, "name")

    if existing:
        # UPDATE
        security = frappe.get_doc("Bid Security", existing)
        security.amount = doc.bond_amount
        security.cpo_number = doc.bond_number
        security.expiry_date = doc.bond_expiry
        security.bank = doc.bank_name
        security.status = doc.bond_status or "Active"
        security.save(ignore_permissions=True)
        
        # Link back if not linked
        if doc.linked_bid_security != existing:
            doc.db_set("linked_bid_security", existing, update_modified=False)
    else:
        # CREATE
        if doc.bank_name and doc.bond_number:
            new_sec = frappe.get_doc({
                "doctype": "Bid Security",
                "tender": doc.name,
                "amount": doc.bond_amount,
                "cpo_number": doc.bond_number,
                "expiry_date": doc.bond_expiry or frappe.utils.add_days(frappe.utils.nowdate(), 30),
                "bank": doc.bank_name,
                "status": doc.bond_status or "Active"
            })
            new_sec.insert(ignore_permissions=True)
            doc.db_set("linked_bid_security", new_sec.name, update_modified=False)
"""

    if frappe.db.exists("Server Script", script_name):
        scr = frappe.get_doc("Server Script", script_name)
        scr.script = script_content
        scr.save(ignore_permissions=True)
    else:
        frappe.get_doc({
            "doctype": "Server Script",
            "name": script_name,
            "script_type": "DocType Event",
            "reference_doctype": "Tender Opportunity",
            "doctype_event": "After Save",
            "script": script_content
        }).insert(ignore_permissions=True)

def setup_bid_security_accounting():
    script_name = "Automate CPO Journal Entry"
    
    script_content = """
# AUTOMATE CPO JOURNAL ENTRY Logic
if doc.amount > 0 and doc.status == "Active" and not doc.journal_entry:
    # 1. CREATE ISSUANCE JOURNAL
    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Bank Entry"
    je.company = frappe.db.get_value("Company", {}, "name") or "BES" # Default to first company
    je.posting_date = frappe.utils.nowdate()
    je.cheque_no = doc.cpo_number
    je.cheque_date = frappe.utils.nowdate()
    je.user_remark = f"CPO Issuance for Tender: {doc.tender} (Ref: {doc.cpo_number})"
    
    # Debit: Earnest Money
    je.append("accounts", {
        "account": "Earnest Money - BES",
        "debit_in_account_currency": doc.amount,
        "description": f"CPO Deposit for {doc.tender}"
    })
    
    # Credit: Bank
    je.append("accounts", {
        "account": "7868687686867 - cbe - BES",
        "credit_in_account_currency": doc.amount,
        "description": f"CPO Payment for {doc.tender}"
    })
    
    je.insert(ignore_permissions=True)
    je.submit() # Auto-submit if permissions allow, or keep as draft? 
    # For automation consistency, we insert. User can submit if required, but usually CPO is a real money move.
    
    doc.db_set("journal_entry", je.name, update_modified=False)
    frappe.msgprint(f"✔ Journal Entry {je.name} created for CPO")

elif doc.status == "Released" and doc.journal_entry and not doc.release_journal_entry:
    # 2. CREATE REVERSAL JOURNAL
    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Bank Entry"
    je.company = frappe.db.get_value("Company", {}, "name") or "BES"
    je.posting_date = frappe.utils.nowdate()
    je.cheque_no = doc.cpo_number
    je.cheque_date = frappe.utils.nowdate()
    je.user_remark = f"CPO Release for Tender: {doc.tender}"
    
    # Debit: Bank
    je.append("accounts", {
        "account": "7868687686867 - cbe - BES",
        "debit_in_account_currency": doc.amount,
        "description": f"CPO Release (Credit back to Bank) for {doc.tender}"
    })
    
    # Credit: Earnest Money
    je.append("accounts", {
        "account": "Earnest Money - BES",
        "credit_in_account_currency": doc.amount,
        "description": f"CPO Release (Clear Earnest Money) for {doc.tender}"
    })
    
    je.insert(ignore_permissions=True)
    doc.db_set("release_journal_entry", je.name, update_modified=False)
    frappe.msgprint(f"✔ Reversal Journal Entry {je.name} created for CPO Release")
"""

    if frappe.db.exists("Server Script", script_name):
        scr = frappe.get_doc("Server Script", script_name)
        scr.script = script_content
        scr.save(ignore_permissions=True)
    else:
        frappe.get_doc({
            "doctype": "Server Script",
            "name": script_name,
            "script_type": "DocType Event",
            "reference_doctype": "Bid Security",
            "doctype_event": "After Save",
            "script": script_content
        }).insert(ignore_permissions=True)

def setup_document_purchase_payment():
    """
    Automate Payment Entry creation when doc_purchase_status changes to 'Funds Released'
    """
    script_name = "Auto Payment Entry - Document Purchase"
    
    script_content = """
# AUTOMATE DOCUMENT PURCHASE PAYMENT ENTRY
if doc.doc_purchase_status == "Funds Released" and doc.document_price > 0 and not doc.doc_purchase_payment_entry:
    # Create Payment Entry
    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = "Pay"
    pe.posting_date = frappe.utils.nowdate()
    pe.company = frappe.db.get_value("Company", {}, "name") or "BES"
    
    # Get default accounts
    company = frappe.db.get_value("Company", {}, "name") or "BES"
    
    # Source: Bank Account (same as CPO)
    pe.paid_from = "7868687686867 - cbe - BES"
    pe.paid_from_account_currency = "ETB"
    
    # Destination: Expense Account (create if doesn't exist)
    expense_account = "Tender Document Purchase - BES"
    if not frappe.db.exists("Account", expense_account):
        # If account doesn't exist, use a generic expense account
        expense_account = frappe.db.get_value("Account", {
            "company": company,
            "account_type": "Expense Account",
            "is_group": 0
        }, "name")
        if not expense_account:
            frappe.throw("No suitable Expense Account found. Please create 'Tender Document Purchase - BES' account.")
    
    pe.paid_to = expense_account
    pe.paid_to_account_currency = "ETB"
    
    # Amounts
    pe.paid_amount = doc.document_price
    pe.received_amount = doc.document_price
    
    # Reference details
    pe.reference_no = doc.purchase_receipt_no or doc.name
    pe.reference_date = doc.purchase_date or frappe.utils.nowdate()
    pe.remarks = f"Auto-payment for tender document purchase: {doc.title}"
    
    # Insert and submit
    pe.insert(ignore_permissions=True)
    pe.submit()
    
    # Link back to Tender Opportunity
    doc.db_set("doc_purchase_payment_entry", pe.name, update_modified=False)
    frappe.msgprint(f"✔ Payment Entry {pe.name} created for document purchase")
"""

    if frappe.db.exists("Server Script", script_name):
        scr = frappe.get_doc("Server Script", script_name)
        scr.script = script_content
        scr.save(ignore_permissions=True)
        print(f"✔ Updated Server Script: {script_name}")
    else:
        frappe.get_doc({
            "doctype": "Server Script",
            "name": script_name,
            "script_type": "DocType Event",
            "reference_doctype": "Tender Opportunity",
            "doctype_event": "After Save",
            "script": script_content,
            "disabled": 0
        }).insert(ignore_permissions=True)
        print(f"✔ Created Server Script: {script_name}")

def setup_notifications():
    """
    Standardize system-wide notifications.
    """
    print("🔔 Setting up Notifications...")

    # 1. Tender Deadline Alert
    if not frappe.db.exists("Notification", "Tender Deadline Alert"):
        frappe.get_doc({
            "doctype": "Notification",
            "name": "Tender Deadline Alert",
            "document_type": "Tender Opportunity",
            "event": "Days Before",
            "days_before_after": 2,
            "date_changed": "submission_deadline",
            "channel": "System Notification",
            "enabled": 1,
            "subject": "Tender Submission Deadline Tomorrow: {{ doc.name }}",
            "message": "The tender <b>{{ doc.title }}</b> is closing tomorrow ({{ doc.submission_deadline }}). Please ensure preparation is complete."
        }).insert(ignore_permissions=True)

    # 2. CPO Expiry Alert
    if not frappe.db.exists("Notification", "CPO Expiry Alert"):
        frappe.get_doc({
            "doctype": "Notification",
            "name": "CPO Expiry Alert",
            "document_type": "Bid Security",
            "event": "Days Before",
            "days_before_after": 7,
            "date_changed": "expiry_date",
            "channel": "System Notification",
            "enabled": 1,
            "subject": "CPO Expiring Soon: {{ doc.name }}",
            "message": "The Bid Security (CPO) for Tender <b>{{ doc.tender }}</b> expires in 7 days."
        }).insert(ignore_permissions=True)

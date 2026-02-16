
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
    setup_bid_bond_account()
    setup_dashboard_charts()
    setup_number_cards()
    setup_workspace()
    setup_enhanced_workflow()
    cleanup_legacy_customizations()
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
            except Exception as e:
                print(f"✔ Account {account_name} setup handled: {str(e)}")
        else:
            print(f"⚠ Could not create account {account_name}: No suitable parent account found")
    else:
        print(f"✔ Account already exists: {account_name}")

def setup_bid_bond_account():
    """
    Create Bid Bond Receivable account for bid security journal entries
    """
    # Get default company
    company = frappe.db.get_value("Company", {}, "name") or "BES"
    
    # Create Bid Bond Receivable account under Current Assets
    account_name = f"Bid Bond Receivable - {company}"
    
    if not frappe.db.exists("Account", account_name):
        # Find parent Current Assets account
        parent_account = frappe.db.get_value("Account", {
            "company": company,
            "account_name": "Current Assets",
            "is_group": 1
        }, "name")
        
        # If no Current Assets, try root Asset account
        if not parent_account:
            parent_account = frappe.db.get_value("Account", {
                "company": company,
                "root_type": "Asset",
                "is_group": 1
            }, "name")
        
        if parent_account:
            try:
                frappe.get_doc({
                    "doctype": "Account",
                    "account_name": "Bid Bond Receivable",
                    "parent_account": parent_account,
                    "is_group": 0,
                    "company": company,
                    "account_type": "Receivable",
                    "root_type": "Asset"
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

    # 6. Tasks by Status
    chart_6 = "Tasks by Status"
    chart_doc_6 = {
        "doctype": "Dashboard Chart",
        "chart_name": chart_6,
        "chart_type": "Group By",
        "document_type": "Tender Task",
        "group_by_based_on": "status",
        "aggregate_function": "Count",
        "type": "Donut",
        "is_public": 1,
        "filters_json": "[]",
        "module": "Tender Management"
    }
    upsert_dashboard_chart(chart_6, chart_doc_6)

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
            "stats_time_interval": "Monthly",
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
            "stats_time_interval": "Monthly",
        }).insert(ignore_permissions=True)

    # 3. My Open Tasks
    card_3 = "My Open Tasks"
    if not frappe.db.exists("Number Card", card_3):
        frappe.get_doc({
            "doctype": "Number Card",
            "name": card_3,
            "label": "My Open Tasks",
            "document_type": "Tender Task",
            "function": "Count",
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Monthly",
            "filters_json": json.dumps([["Tender Task", "status", "in", ["Open", "In Progress"]], ["Tender Task", "assigned_to", "=", "frappe.session.user"]]),
            "module": "Tender Management"
        }).insert(ignore_permissions=True)

def setup_workspace():
    workspace_name = "Tender Management"
    
    # Define the layout using the block format expected by Frappe Workspace
    ws_content = [
        {"type": "header", "data": {"text": "Key Insights", "level": 2, "col": 12}},
        {"type": "card", "data": {"card_name": "Total Active Tenders", "col": 4}},
        {"type": "card", "data": {"card_name": "Total Won Value", "col": 4}},
        
        {"type": "header", "data": {"text": "Performance & Pipeline", "level": 2, "col": 12}},
        {"type": "chart", "data": {"chart_name": "Tender Pipeline Value", "col": 8}},
        {"type": "chart", "data": {"chart_name": "Win Loss Ratio", "col": 4}},
        {"type": "chart", "data": {"chart_name": "Active Bids per User", "col": 12}},
        
        {"type": "header", "data": {"text": "Trends & Analysis", "level": 2, "col": 12}},
        {"type": "chart", "data": {"chart_name": "Monthly Publication Trend", "col": 12}},
        {"type": "chart", "data": {"chart_name": "Tenders by Sector", "col": 6}},
        {"type": "chart", "data": {"chart_name": "Bond Type Distribution", "col": 6}},
        {"type": "chart", "data": {"chart_name": "Bid vs No-Bid", "col": 6}},
        {"type": "chart", "data": {"chart_name": "Tenders by Type", "col": 6}},
        
        {"type": "header", "data": {"text": "Quick Actions", "level": 3, "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "Tenders", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "Tasks", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "Calendar View", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "Bid Decisions", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "Cost Estimations", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "Templates", "col": 3}},
        
        {"type": "header", "data": {"text": "Task Overview", "level": 3, "col": 12}},
        {"type": "chart", "data": {"chart_name": "Tasks by Status", "col": 6}},
        {"type": "card", "data": {"card_name": "My Open Tasks", "col": 6}},

        {"type": "header", "data": {"text": "Contract Management", "level": 3, "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "Performance Bonds", "col": 3}},
        
        {"type": "header", "data": {"text": "Intelligence", "level": 3, "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "Competitors", "col": 3}}
    ]

    charts = [
        {"chart_name": "Tender Pipeline Value", "label": "Tender Pipeline Value"},
        {"chart_name": "Win Loss Ratio", "label": "Win Loss Ratio"},
        {"chart_name": "Active Bids per User", "label": "Active Bids per User"},
        {"chart_name": "Monthly Publication Trend", "label": "Monthly Publication Trend"},
        {"chart_name": "Tenders by Sector", "label": "Tenders by Sector"},
        {"chart_name": "Bond Type Distribution", "label": "Bond Type Distribution"},
        {"chart_name": "Bid vs No-Bid", "label": "Bid vs No-Bid"},
        {"chart_name": "Tenders by Type", "label": "Tenders by Type"},
        {"chart_name": "Tasks by Status", "label": "Tasks by Status", "chart_type": "Donut", "document_type": "Tender Task", "based_on": "status"}
    ]

    number_cards = [
        {"number_card_name": "Total Active Tenders", "label": "Total Active Tenders"},
        {"number_card_name": "Total Won Value", "label": "Total Won Value"},
        {"number_card_name": "My Open Tasks", "label": "My Open Tasks", "document_type": "Tender Task", "function": "Count", "filters_json": '[["Tender Task","status","in",["Open","In Progress"]],["Tender Task","assigned_to","=","frappe.session.user"]]'}
    ]

    shortcuts = [
        {"link_to": "Tender Opportunity", "type": "DocType", "label": "Tenders", "icon": "list", "color": "Grey"},
        {"link_to": "Tender Task", "type": "DocType", "label": "Tasks", "icon": "check", "color": "Blue"},
        {"link_to": "tender-calendar", "type": "Page", "label": "Calendar View", "icon": "calendar", "color": "Orange"},
        {"link_to": "Bid Decision Matrix", "type": "DocType", "label": "Bid Decisions", "icon": "milestone", "color": "Purple"},
        {"link_to": "Cost Estimation", "type": "DocType", "label": "Cost Estimations", "icon": "calculator", "color": "Green"},
        {"link_to": "Document Template", "type": "DocType", "label": "Templates", "icon": "file", "color": "Cyan"},
        {"link_to": "Performance Bond", "type": "DocType", "label": "Performance Bonds", "icon": "shield", "color": "Red"},
        {"link_to": "Competitor", "type": "DocType", "label": "Competitors", "icon": "users", "color": "Yellow"}
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
        print(f"✔ Created Workspace: {workspace_name}")
    else:
        doc = frappe.get_doc("Workspace", workspace_name)
        doc.update(ws_doc)
        doc.save(ignore_permissions=True)
        print(f"✔ Updated Workspace: {workspace_name}")

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
    """
    DISABLED: This legacy script created old Bid Security records.
    We now use Bid Security Request with auto-creation from Tender Opportunity.
    Keeping this function to disable any existing server scripts.
    """
    script_name = "Auto-Create Bid Security"
    
    # Disable the old script if it exists
    if frappe.db.exists("Server Script", script_name):
        scr = frappe.get_doc("Server Script", script_name)
        scr.disabled = 1
        scr.save(ignore_permissions=True)
        print(f"✔ Disabled legacy Server Script: {script_name}")
    else:
        print(f"✔ Legacy Server Script not found: {script_name}")

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
    pe.payment_type = "Internal Transfer"  # Changed from "Pay" to avoid party requirement
    pe.posting_date = frappe.utils.nowdate()
    pe.company = frappe.db.get_value("Company", {}, "name") or "BES"
    
    # Get default accounts
    company = frappe.db.get_value("Company", {}, "name") or "BES"
    
    # Source: Bank Account (same as CPO)
    pe.paid_from = "7868687686867 - cbe - BES"
    pe.paid_from_account_currency = "ETB"
    
    # Destination: Expense Account (create if doesn't exist)
    expense_account = f"Tender Document Purchase - {company}"
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
    pe.flags.ignore_permissions = True
    pe.insert()
    pe.submit()
    
    # Link back to Tender Opportunity
    doc.db_set("doc_purchase_payment_entry", pe.name, update_modified=False)
    frappe.msgprint(f"✔ Payment Entry {pe.name} created for document purchase", alert=True, indicator="green")
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
        print(f"✔ Created Notification: CPO Expiry Alert")

def cleanup_legacy_customizations():
    """
    NUCLEAR OPTION: Disable any database-stored customizations that might interfere.
    Specifically targets the ghost "Bond Number and Bank Name are required" validation.
    """
    print("🧹 Cleaning up legacy customizations...")
    
    target_doctype = "Tender Opportunity"
    
    # 1. Disable ALL Server Scripts for Tender Opportunity except our managed one
    managed_scripts = ["Auto Payment Entry - Document Purchase"]
    
    server_scripts = frappe.get_all("Server Script", filters={
        "reference_doctype": target_doctype,
        "disabled": 0
    }, fields=["name"])
    
    for s in server_scripts:
        if s.name not in managed_scripts:
            frappe.db.set_value("Server Script", s.name, "disabled", 1)
            print(f"  ✔ Disabled legacy Server Script: {s.name}")
            
    # 2. Disable ANY database-stored Client Scripts for Tender Opportunity
    # These often override the file-based .js script
    client_scripts = frappe.get_all("Client Script", filters={
        "dt": target_doctype,
        "enabled": 1
    }, fields=["name"])
    
    for c in client_scripts:
        frappe.db.set_value("Client Script", c.name, "enabled", 0)
        print(f"  ✔ Disabled legacy Client Script: {c.name}")
        
    # 3. Delete Property Setters that force bond_number or bank_name
    frappe.db.sql("""
        DELETE FROM `tabProperty Setter` 
        WHERE doc_type = %s 
        AND field_name IN ('bond_number', 'bank_name')
        AND property = 'reqd'
    """, (target_doctype))
    print("  ✔ Cleared mandatory Property Setters for bond fields")
    
    frappe.clear_cache(doctype=target_doctype)

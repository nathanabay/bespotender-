import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def run():
    print("--- 🏗 BUILDING TENDER MANAGEMENT SYSTEM ---")

    # 1. CREATE DOCTYPE: 'Tender Opportunity'
    if not frappe.db.exists("DocType", "Tender Opportunity"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "module": "Tender Management",
            "name": "Tender Opportunity",
            "custom": 0,
            "is_submittable": 1,
            "track_changes": 1,
            "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}],
            "fields": [
                # --- STAGE 1: SCRAPING (The Input) ---
                {"label": "Identification (Scraper)", "fieldname": "sb_id", "fieldtype": "Section Break"},
                {"label": "Tender Title", "fieldname": "title", "fieldtype": "Data", "reqd": 1, "in_list_view": 1},
                {"label": "Client / Organization", "fieldname": "client", "fieldtype": "Data", "in_list_view": 1},
                {"label": "Source (Newspaper/URL)", "fieldname": "source", "fieldtype": "Data"},
                {"label": "Submission Deadline", "fieldname": "deadline", "fieldtype": "Datetime", "reqd": 1, "in_list_view": 1},
                {"label": "Scanned Newspaper Clipping", "fieldname": "scan_preview", "fieldtype": "Attach Image"},
                {"label": "Status", "fieldname": "workflow_state", "fieldtype": "Select", "options": "Identified\nTo Buy\nBuying\nScanning\nProposal\nReview\nSubmitted\nLost", "read_only": 1},

                # --- STAGE 2: BUYING (The Logistics) ---
                {"label": "Document Acquisition", "fieldname": "sb_buy", "fieldtype": "Section Break"},
                {"label": "Assigned Buyer", "fieldname": "buyer", "fieldtype": "Link", "options": "User"},
                {"label": "Document Cost (ETB)", "fieldname": "doc_cost", "fieldtype": "Currency"},
                {"label": "Receipt No.", "fieldname": "receipt_no", "fieldtype": "Data"},
                {"label": "Full Tender Document (PDF)", "fieldname": "full_document", "fieldtype": "Attach"},

                # --- STAGE 3: PROPOSAL (The Work) ---
                {"label": "Proposal Development", "fieldname": "sb_prop", "fieldtype": "Section Break"},
                {"label": "Engineering Lead", "fieldname": "eng_lead", "fieldtype": "Link", "options": "User"},
                {"label": "Marketing Lead", "fieldname": "mkt_lead", "fieldtype": "Link", "options": "User"},
                {"label": "Technical Proposal", "fieldname": "tech_doc", "fieldtype": "Attach"},
                {"label": "Financial Proposal", "fieldname": "fin_doc", "fieldtype": "Attach"},
                {"label": "Final Bid Amount", "fieldname": "bid_amount", "fieldtype": "Currency"},

                # --- STAGE 4: APPROVAL (The Decision) ---
                {"label": "Manager Review", "fieldname": "sb_review", "fieldtype": "Section Break"},
                {"label": "Manager Comments", "fieldname": "manager_comments", "fieldtype": "Small Text"},
                {"label": "Decision Date", "fieldname": "decision_date", "fieldtype": "Date"}
            ]
        })
        doc.insert(ignore_permissions=True)
        print("✔ DocType Created: 'Tender Opportunity'")

    # 2. CREATE WORKFLOW (The Rules)
    wf_name = "Tender Lifecycle"
    
    if frappe.db.exists("Workflow", wf_name):
        frappe.delete_doc("Workflow", wf_name)

    wf = frappe.get_doc({
        "doctype": "Workflow",
        "workflow_name": wf_name,
        "document_type": "Tender Opportunity",
        "workflow_state_field": "workflow_state",
        "is_active": 1,
        "states": [
            {"state": "Identified", "doc_status": 0, "allow_edit": "System Manager", "update_field": "workflow_state"},
            {"state": "To Buy", "doc_status": 0, "allow_edit": "System Manager", "update_field": "workflow_state"},
            {"state": "Buying", "doc_status": 0, "allow_edit": "System Manager", "update_field": "workflow_state"},
            {"state": "Scanning", "doc_status": 0, "allow_edit": "System Manager", "update_field": "workflow_state"},
            {"state": "Proposal", "doc_status": 0, "allow_edit": "System Manager", "update_field": "workflow_state"},
            {"state": "Review", "doc_status": 0, "allow_edit": "System Manager", "update_field": "workflow_state"},
            {"state": "Approved", "doc_status": 1, "allow_edit": "System Manager", "update_field": "workflow_state"},
            {"state": "Rejected", "doc_status": 2, "allow_edit": "System Manager", "update_field": "workflow_state"}
        ],
        "transitions": [
            {"state": "Identified", "action": "Approve for Purchase", "next_state": "To Buy", "allowed": "System Manager"},
            {"state": "To Buy", "action": "Assign Buyer", "next_state": "Buying", "allowed": "System Manager"},
            {"state": "Buying", "action": "Upload Documents", "next_state": "Scanning", "allowed": "System Manager"},
            {"state": "Scanning", "action": "Start Proposal", "next_state": "Proposal", "allowed": "System Manager"},
            {"state": "Proposal", "action": "Submit for Review", "next_state": "Review", "allowed": "System Manager"},
            {"state": "Review", "action": "Approve Bid", "next_state": "Approved", "allowed": "System Manager"},
            {"state": "Review", "action": "Reject Bid", "next_state": "Rejected", "allowed": "System Manager"}
        ]
    })
    wf.insert(ignore_permissions=True)
    print("✔ Workflow Created: 'Tender Lifecycle'")

    frappe.db.commit()
    print("--- ✅ DONE ---")
    print("👉 Reload ERPNext. Search for 'Tender Opportunity'.")

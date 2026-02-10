import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
import json

def run():
    print("--- 🏗 STARTING SOP RECONSTRUCTION (V2) ---")

    # 1. UPGRADE DOCTYPE FIELDS
    # ... (Same logic as before, just ensuring fields exist)
    fields = {
        "Tender Opportunity": [
            {"fieldname": "sector", "label": "Sector", "fieldtype": "Select", "options": "Construction\nElectro-Mechanical\nGeneral Supply", "insert_after": "tender_number"},
            {"fieldname": "sb_purchase", "label": "3.3 Tender Purchase", "fieldtype": "Section Break", "insert_after": "workflow_state"},
            {"fieldname": "tender_fee_required", "label": "Tender Fee Required?", "fieldtype": "Check", "insert_after": "sb_purchase"},
            {"fieldname": "tender_fee_amount", "label": "Tender Fee Amount", "fieldtype": "Currency", "depends_on": "eval:doc.tender_fee_required==1", "insert_after": "tender_fee_required"},
            {"fieldname": "payment_entry", "label": "Payment Entry (Record)", "fieldtype": "Link", "options": "Payment Entry", "insert_after": "tender_fee_amount"},
            {"fieldname": "sb_bond", "label": "3.4 Bid Bond Details", "fieldtype": "Section Break", "insert_after": "payment_entry"},
            {"fieldname": "bond_type", "label": "Bond Type", "fieldtype": "Select", "options": "Bank Guarantee\nInsurance Bond\nCPO", "insert_after": "sb_bond"},
            {"fieldname": "bond_percentage", "label": "Bond Percentage (%)", "fieldtype": "Percent", "insert_after": "bond_type"},
            {"fieldname": "bond_amount", "label": "Bond Amount", "fieldtype": "Currency", "insert_after": "bond_percentage"},
            {"fieldname": "bond_number", "label": "Bond Number", "fieldtype": "Data", "insert_after": "bond_amount"},
            {"fieldname": "bond_expiry", "label": "Expiry Date", "fieldtype": "Date", "insert_after": "bond_number"},
            {"fieldname": "bond_status", "label": "Bond Status", "fieldtype": "Select", "options": "Pending\nActive\nReleased\nConfiscated", "default": "Pending", "insert_after": "bond_expiry"},
            {"fieldname": "sb_costing", "label": "3.5 Costing & Pricing", "fieldtype": "Section Break", "insert_after": "bond_status"},
            {"fieldname": "material_cost", "label": "Material Cost", "fieldtype": "Currency", "insert_after": "sb_costing"},
            {"fieldname": "labor_cost", "label": "Labor Cost", "fieldtype": "Currency", "insert_after": "material_cost"},
            {"fieldname": "overheads", "label": "Overheads", "fieldtype": "Currency", "insert_after": "labor_cost"},
            {"fieldname": "risk_contingency", "label": "Risk Contingency", "fieldtype": "Currency", "insert_after": "overheads"},
            {"fieldname": "final_bid_price", "label": "Final Bid Price", "fieldtype": "Currency", "read_only": 1, "insert_after": "risk_contingency"}
        ]
    }
    create_custom_fields(fields)
    print("✔ Doctype Updated")

    # 2. WORKFLOW RECONSTRUCTION
    wf_name = "Tender Register Workflow"
    frappe.db.delete("Workflow", {"document_type": "Tender Opportunity"})

    # Corrected States with Valid Colors
    sop_states = [
        ("Draft", "Inverse", 0),          # Was Gray
        ("Under Evaluation", "Info", 0),  # Was Blue
        ("Approved to Bid", "Success", 0),# Was Cyan
        ("Tender Purchased", "Primary", 0),# Was Purple
        ("Bid Bond Issued", "Primary", 0),
        ("Technical Preparation", "Warning", 0), # Was Orange
        ("Financial Preparation", "Warning", 0),
        ("Ready for Submission", "Danger", 0), # Was Pink (Using Danger/Red for high alert)
        ("Submitted", "Primary", 1),
        ("Under Client Evaluation", "Warning", 1), # Was Yellow
        ("Won", "Success", 1),
        ("Lost", "Danger", 2)
    ]

    wfs_list = []
    for s_name, s_style, s_docstatus in sop_states:
        if not frappe.db.exists("Workflow State", s_name):
            frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": s_name, "style": s_style}).insert()
        
        wfs_list.append({
            "state": s_name,
            "doc_status": s_docstatus,
            "allow_edit": "System Manager",
            "update_field": "workflow_state"
        })

    # Create Actions (Crucial Step!)
    actions = ["Start Evaluation", "Approve Go", "Confirm Purchase", "Issue Bond", "Start Technical", "Start Financial", "Finalize", "Submit Bid", "Client Review", "Award Tender", "Regret"]
    for a in actions:
        if not frappe.db.exists("Workflow Action", a):
            frappe.db.sql("INSERT INTO `tabWorkflow Action` (name, creation, modified) VALUES (%s, NOW(), NOW())", (a,))

    frappe.db.commit()

    # Link Workflow
    wf = frappe.get_doc({
        "doctype": "Workflow",
        "workflow_name": wf_name,
        "document_type": "Tender Opportunity",
        "workflow_state_field": "workflow_state",
        "is_active": 1,
        "states": wfs_list,
        "transitions": [
            {"state": "Draft", "action": "Start Evaluation", "next_state": "Under Evaluation", "allowed": "System Manager"},
            {"state": "Under Evaluation", "action": "Approve Go", "next_state": "Approved to Bid", "allowed": "System Manager"},
            {"state": "Approved to Bid", "action": "Confirm Purchase", "next_state": "Tender Purchased", "allowed": "System Manager"},
            {"state": "Tender Purchased", "action": "Issue Bond", "next_state": "Bid Bond Issued", "allowed": "System Manager"},
            {"state": "Bid Bond Issued", "action": "Start Technical", "next_state": "Technical Preparation", "allowed": "System Manager"},
            {"state": "Technical Preparation", "action": "Start Financial", "next_state": "Financial Preparation", "allowed": "System Manager"},
            {"state": "Financial Preparation", "action": "Finalize", "next_state": "Ready for Submission", "allowed": "System Manager"},
            {"state": "Ready for Submission", "action": "Submit Bid", "next_state": "Submitted", "allowed": "System Manager"},
            {"state": "Submitted", "action": "Client Review", "next_state": "Under Client Evaluation", "allowed": "System Manager"},
            {"state": "Under Client Evaluation", "action": "Award Tender", "next_state": "Won", "allowed": "System Manager"},
            {"state": "Under Client Evaluation", "action": "Regret", "next_state": "Lost", "allowed": "System Manager"},
        ]
    })
    wf.insert(ignore_permissions=True)
    print("✔ Workflow Updated")

    # 3. DASHBOARD INJECTION
    ws_name = "Tender Management"
    if frappe.db.exists("Workspace", ws_name):
        frappe.delete_doc("Workspace", ws_name, force=True)

    ws_content = [
        {"type": "header", "data": {"text": "SOP Dashboard (Sec 5)", "level": 2}},
        {"type": "chart", "data": {"chart_name": "Tender Pipeline Value", "col": 12}},
        {"type": "chart", "data": {"chart_name": "Win Loss Ratio", "col": 6}},
        {"type": "header", "data": {"text": "Process Control", "level": 3}},
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "label": "Active Tenders", "stats_filter": json.dumps({"workflow_state": ["!=", "Submitted"]})}},
        {"type": "shortcut", "data": {"link_to": "Bid Security", "label": "Bond Tracking", "icon": "lock"}}
    ]

    frappe.get_doc({
        "doctype": "Workspace",
        "name": ws_name,
        "label": ws_name,
        "title": ws_name,
        "module": "Tender Management",
        "public": 1,
        "content": json.dumps(ws_content)
    }).insert(ignore_permissions=True)
    
    frappe.db.commit()
    print("--- ✅ SOP V2 COMPLETE ---")

if __name__ == "__main__":
    run()

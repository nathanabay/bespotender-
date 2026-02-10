import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def run():
    print("--- 🏗 STARTING SOP RECONSTRUCTION ---")

    # ==============================================================================
    # 1. UPGRADE DOCTYPE: TENDER OPPORTUNITY (Manual Sec 3.1 - 3.5)
    # ==============================================================================
    # We are adding specific fields for Fee, Bond, and Costing directly to the Tender.
    
    fields = {
        "Tender Opportunity": [
            # 3.1 Basic Info (Already largely exists, ensuring specific naming)
            {"fieldname": "sector", "label": "Sector", "fieldtype": "Select", "options": "Construction\nElectro-Mechanical\nGeneral Supply", "insert_after": "tender_number"},
            
            # 3.3 Tender Purchase Details
            {"fieldname": "sb_purchase", "label": "3.3 Tender Purchase", "fieldtype": "Section Break", "insert_after": "workflow_state"},
            {"fieldname": "tender_fee_required", "label": "Tender Fee Required?", "fieldtype": "Check", "insert_after": "sb_purchase"},
            {"fieldname": "tender_fee_amount", "label": "Tender Fee Amount", "fieldtype": "Currency", "depends_on": "eval:doc.tender_fee_required==1", "insert_after": "tender_fee_required"},
            {"fieldname": "payment_entry", "label": "Payment Entry (Record)", "fieldtype": "Link", "options": "Payment Entry", "insert_after": "tender_fee_amount"},
            {"fieldname": "receipt_attachment", "label": "Receipt Attachment", "fieldtype": "Attach", "insert_after": "payment_entry"},

            # 3.4 Bid Bond Details (Manual implies these are on the main doc)
            {"fieldname": "sb_bond", "label": "3.4 Bid Bond Details", "fieldtype": "Section Break", "insert_after": "receipt_attachment"},
            {"fieldname": "bond_type", "label": "Bond Type", "fieldtype": "Select", "options": "Bank Guarantee\nInsurance Bond\nCPO", "insert_after": "sb_bond"},
            {"fieldname": "bond_percentage", "label": "Bond Percentage (%)", "fieldtype": "Percent", "insert_after": "bond_type"},
            {"fieldname": "bond_amount", "label": "Bond Amount", "fieldtype": "Currency", "insert_after": "bond_percentage"},
            {"fieldname": "bond_number", "label": "Bond Number", "fieldtype": "Data", "insert_after": "bond_amount"},
            {"fieldname": "bond_expiry", "label": "Expiry Date", "fieldtype": "Date", "insert_after": "bond_number"},
            {"fieldname": "bond_status", "label": "Bond Status", "fieldtype": "Select", "options": "Pending\nActive\nReleased\nConfiscated", "default": "Pending", "insert_after": "bond_expiry"},

            # 3.5 Costing & Pricing
            {"fieldname": "sb_costing", "label": "3.5 Costing & Pricing", "fieldtype": "Section Break", "insert_after": "bond_status"},
            {"fieldname": "material_cost", "label": "Material Cost", "fieldtype": "Currency", "insert_after": "sb_costing"},
            {"fieldname": "labor_cost", "label": "Labor Cost", "fieldtype": "Currency", "insert_after": "material_cost"},
            {"fieldname": "overheads", "label": "Overheads", "fieldtype": "Currency", "insert_after": "labor_cost"},
            {"fieldname": "risk_contingency", "label": "Risk Contingency", "fieldtype": "Currency", "insert_after": "overheads"},
            {"fieldname": "final_bid_price", "label": "Final Bid Price", "fieldtype": "Currency", "read_only": 1, "insert_after": "risk_contingency"} # Will be calc via script
        ]
    }
    
    create_custom_fields(fields)
    print("✔ Doctype Updated: 3.1 - 3.5 Fields Added")

    # ==============================================================================
    # 2. WORKFLOW RECONSTRUCTION (Manual Sec 4)
    # ==============================================================================
    # The manual lists 12 specific states. We must recreate the workflow to match.
    
    wf_name = "Tender Register Workflow" # Renaming to match manual
    
    # Delete old workflow to avoid conflicts
    frappe.db.delete("Workflow", {"document_type": "Tender Opportunity"}) 

    # Define States from Manual Section 4
    sop_states = [
        ("Draft", "Gray", 0),
        ("Under Evaluation", "Blue", 0),
        ("Approved to Bid", "Cyan", 0),
        ("Tender Purchased", "Purple", 0),
        ("Bid Bond Issued", "Purple", 0),
        ("Technical Preparation", "Orange", 0),
        ("Financial Preparation", "Orange", 0),
        ("Ready for Submission", "Pink", 0),
        ("Submitted", "Primary", 1),
        ("Under Client Evaluation", "Yellow", 1),
        ("Won", "Green", 1),
        ("Lost", "Red", 2)
    ]

    # Create States
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

    # Create Workflow
    wf = frappe.get_doc({
        "doctype": "Workflow",
        "workflow_name": wf_name,
        "document_type": "Tender Opportunity",
        "workflow_state_field": "workflow_state",
        "is_active": 1,
        "states": wfs_list,
        "transitions": [
            # Defined flow based on Manual Sec 4
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
    wf.save(ignore_permissions=True)
    print("✔ Workflow Updated: 12-Step SOP Flow Active")

    # ==============================================================================
    # 3. DASHBOARD (Manual Sec 5)
    # ==============================================================================
    import json
    
    # 3.1 Create Charts (Pipeline, Win Ratio, Bond Exposure)
    charts = [
        {
            "name": "SOP Total Bid Value",
            "type": "Group By",
            "group_by": "workflow_state",
            "agg_on": "final_bid_price",
            "agg_func": "Sum",
            "chart_type": "Bar"
        },
        {
            "name": "SOP Win Ratio",
            "type": "Count",
            "group_by": "workflow_state",
            "agg_on": None,
            "agg_func": None,
            "chart_type": "Donut",
            "filters": [["Tender Opportunity", "workflow_state", "in", ["Won", "Lost"]]]
        },
        {
            "name": "SOP Bond Exposure",
            "type": "Group By",
            "group_by": "bond_type",
            "agg_on": "bond_amount",
            "agg_func": "Sum",
            "chart_type": "Percentage"
        }
    ]

    for c in charts:
        if frappe.db.exists("Dashboard Chart", c["name"]):
            frappe.delete_doc("Dashboard Chart", c["name"])
            
        doc = {
            "doctype": "Dashboard Chart",
            "chart_name": c["name"],
            "chart_type": c["type"],
            "document_type": "Tender Opportunity",
            "type": c["chart_type"],
            "is_public": 1,
            "timeseries": 0,
            "filters_json": json.dumps(c.get("filters", []))
        }
        
        if c["type"] == "Group By":
            doc["group_by_based_on"] = c["group_by"]
            doc["aggregate_function_based_on"] = c["agg_on"]
            doc["aggregate_function"] = c["agg_func"]
        else:
            doc["group_by_based_on"] = c["group_by"]
            doc["based_on"] = "creation" # Required for Count

        frappe.get_doc(doc).insert(ignore_permissions=True)
        print(f"✔ Chart Created: {c['name']}")

    # 3.2 Create Workspace
    ws_name = "Tender Management"
    if frappe.db.exists("Workspace", ws_name):
        frappe.delete_doc("Workspace", ws_name, force=True)

    ws_content = [
        {"type": "header", "data": {"text": "Performance Dashboard (SOP Sec 5)", "level": 2}},
        {"type": "chart", "data": {"chart_name": "SOP Total Bid Value", "col": 12}},
        {"type": "chart", "data": {"chart_name": "SOP Win Ratio", "col": 6}},
        {"type": "chart", "data": {"chart_name": "SOP Bond Exposure", "col": 6}},
        {"type": "header", "data": {"text": "Deadlines This Week", "level": 3}},
        {"type": "shortcut", "data": {"link_to": "Tender Opportunity", "label": "Tenders Closing Soon", "stats_filter": json.dumps({"workflow_state": ["!=", "Submitted"]})}}
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
    print("--- ✅ SOP RECONSTRUCTION COMPLETE ---")

if __name__ == "__main__":
    run()

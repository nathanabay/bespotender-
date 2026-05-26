import frappe

def run():
    print("--- 📑 FIXING FORM SEQUENCE (PROPOSAL & COSTING) ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. HARVEST EXISTING FIELDS
    field_map = {f.fieldname: f for f in doc.fields}
    
    # 2. DEFINE THE LAYOUT
    layout_plan = [
        # ================= TAB 1: IDENTIFICATION =================
        {"type": "Tab Break", "label": "Identification & Qualification", "fieldname": "tab_identification"},
        
        {"type": "Section Break", "label": "Identification", "fieldname": "sec_identification"},
        "title", "naming_series", "tender_number", "organization", "sector", "status", "workflow_state", "url", "publication_date",
        
        {"type": "Section Break", "label": "Go / No-Go Decision", "fieldname": "sec_go_no_go"},
        "bid_probability_score", "decision_matrix", "decision_notes",
        
        {"type": "Section Break", "label": "Purchase & Bond", "fieldname": "sec_purchase_bond"},
        "purchase_price", "purchase_receipt_no", "purchase_date",
        "bond_type", "bond_amount", "bond_percentage", "bond_number", "bank_name", "bond_expiry",
        
        {"type": "Section Break", "label": "Dates", "fieldname": "sec_dates"},
        "site_visit_date", "pre_bid_meeting_date", "clarification_deadline",

        # ================= TAB 2: PROPOSAL & COSTING (REORDERED) =================
        {"type": "Tab Break", "label": "Proposal & Costing", "fieldname": "tab_proposal"},
        
        {"type": "Section Break", "label": "Budget & Planning", "fieldname": "sec_budget_planning"},
        "budget_source", "project_duration_months", "payment_terms",
        
        {"type": "Section Break", "label": "Costing & Pricing", "fieldname": "sec_costing_pricing"},
        "estimated_cost", "margin_percentage", "final_bid_price",
        
        {"type": "Section Break", "label": "Proposal Development", "fieldname": "sec_proposal_dev"},
        "win_themes", "client_pain_points",
        
        {"type": "Section Break", "label": "BOQ Items", "fieldname": "sec_boq_items"},
        "items",

        # ================= TAB 3: COMPLIANCE =================
        {"type": "Tab Break", "label": "Compliance & Review", "fieldname": "tab_compliance"},
        
        {"type": "Section Break", "label": "Competition", "fieldname": "sec_competition"},
        "competitors",
        
        {"type": "Section Break", "label": "Checklists & Analysis", "fieldname": "sec_analysis"},
        "required_documents",
        "loss_reason", "debrief_notes"
    ]

    # 3. REBUILD FIELDS
    new_fields = []
    
    for item in layout_plan:
        if isinstance(item, dict):
            # Create structural element
            new_row = frappe.new_doc("DocField")
            new_row.fieldtype = item.get("type")
            new_row.label = item.get("label")
            new_row.fieldname = item.get("fieldname")
            new_fields.append(new_row)
        
        elif isinstance(item, str):
            fieldname = item
            if fieldname in field_map:
                new_fields.append(field_map[fieldname])
                del field_map[fieldname]
            else:
                # Auto-create if somehow missing
                print(f"   + Re-creating missing field: {fieldname}")
                ft = "Data"
                if "date" in fieldname: ft = "Date"
                elif "price" in fieldname or "amount" in fieldname: ft = "Currency"
                elif "items" in fieldname: ft = "Table"
                
                new_row = frappe.new_doc("DocField")
                new_row.fieldname = fieldname
                new_row.label = fieldname.replace("_", " ").title()
                new_row.fieldtype = ft
                if ft == "Table": new_row.options = "Tender Competitor"
                new_fields.append(new_row)

    # 4. APPEND LEFTOVERS
    if field_map:
        tab_break = frappe.new_doc("DocField")
        tab_break.fieldtype = "Tab Break"
        tab_break.label = "Other Details"
        tab_break.fieldname = "tab_other_details"
        new_fields.append(tab_break)
        
        for fname, fdoc in field_map.items():
            if fdoc.fieldtype not in ["Tab Break", "Section Break", "Column Break"]:
                new_fields.append(fdoc)

    # 5. SAVE
    doc.fields = new_fields
    doc.save(ignore_permissions=True)
    print("--- ✅ FORM SEQUENCE UPDATED ---")

if __name__ == "__main__":
    run()

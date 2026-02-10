import frappe

def run():
    print("--- 📑 REORGANIZING TENDER OPPORTUNITY FORM (FINAL V4) ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. HARVEST EXISTING FIELDS
    field_map = {f.fieldname: f for f in doc.fields}
    
    # 2. DEFINE THE LAYOUT (With Safe Fieldnames)
    layout_plan = [
        # ================= TAB 1 =================
        {"type": "Tab Break", "label": "Identification & Qualification", "fieldname": "tab_identification"},
        
        {"type": "Section Break", "label": "Identification", "fieldname": "sec_identification"},
        "title", "naming_series", "tender_number", "organization", "sector", "status", "workflow_state", "url", "publication_date",
        
        {"type": "Section Break", "label": "Go / No-Go Decision", "fieldname": "sec_go_no_go"}, # SAFE NAME
        "bid_probability_score", "decision_matrix", "decision_notes",
        
        {"type": "Section Break", "label": "Purchase & Bond", "fieldname": "sec_purchase_bond"},
        "purchase_price", "purchase_receipt_no", "purchase_date",
        "bond_type", "bond_amount", "bond_percentage", "bond_number", "bank_name", "bond_expiry",
        
        {"type": "Section Break", "label": "Dates", "fieldname": "sec_dates"},
        "site_visit_date", "pre_bid_meeting_date", "clarification_deadline",

        # ================= TAB 2 =================
        {"type": "Tab Break", "label": "Proposal & Costing", "fieldname": "tab_proposal"},
        
        {"type": "Section Break", "label": "Strategy", "fieldname": "sec_strategy"},
        "win_themes", "client_pain_points",
        
        {"type": "Section Break", "label": "Planning", "fieldname": "sec_planning"},
        "budget_source", "project_duration_months", "payment_terms",
        
        {"type": "Section Break", "label": "Financials", "fieldname": "sec_financials"},
        "estimated_cost", "margin_percentage", "final_bid_price",
        "items",

        # ================= TAB 3 =================
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
            # Create Section/Tab Break
            new_row = frappe.new_doc("DocField")
            new_row.fieldtype = item.get("type")
            new_row.label = item.get("label")
            new_row.fieldname = item.get("fieldname") # Explicitly set safe name
            new_fields.append(new_row)
        
        elif isinstance(item, str):
            fieldname = item
            if fieldname in field_map:
                new_fields.append(field_map[fieldname])
                del field_map[fieldname]
            else:
                # AUTO CREATE MISSING FIELD
                ft = "Data"
                if "date" in fieldname: ft = "Date"
                elif "price" in fieldname or "amount" in fieldname or "cost" in fieldname: ft = "Currency"
                elif "notes" in fieldname: ft = "Small Text"
                elif "items" in fieldname or "matrix" in fieldname or "competitor" in fieldname: ft = "Table"
                
                print(f"   + Creating: {fieldname} ({ft})")
                
                new_row = frappe.new_doc("DocField")
                new_row.fieldname = fieldname
                new_row.label = fieldname.replace("_", " ").title()
                new_row.fieldtype = ft
                if ft == "Table": new_row.options = "Tender Competitor" # Placeholder
                
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
    print("--- ✅ FORM RESTRUCTURED SUCCESSFULLY ---")

if __name__ == "__main__":
    run()

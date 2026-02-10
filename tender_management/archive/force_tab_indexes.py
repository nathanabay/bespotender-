import frappe

def run():
    print("--- 🔢 FORCING FIELD INDEXES (SORT ORDER) ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. PRESERVE DATA FIELD SETTINGS
    # We grab existing field objects to keep their types/options safe
    field_repo = {f.fieldname: f for f in doc.fields}

    # 2. DEFINE THE STRICT ORDER (Fieldnames Only)
    # This list represents the exact visual order we want.
    target_order = [
        # --- TAB 1 ---
        {"name": "tab_identification", "type": "Tab Break", "label": "Overview"}, # RENAMED TO OVERVIEW
        
        {"name": "sec_id", "type": "Section Break", "label": "Tender Details"},
        "naming_series", "title", "tender_number", "organization", "sector", "status", "workflow_state",
        
        {"name": "sec_dates", "type": "Section Break", "label": "Key Dates"},
        "publication_date", "site_visit_date", "pre_bid_meeting_date", "clarification_deadline", "submission_deadline",
        
        {"name": "sec_bond", "type": "Section Break", "label": "Bond & Purchase"},
        "purchase_price", "bond_amount", "bond_number", "bank_name", "bond_expiry",
        
        {"name": "sec_decision", "type": "Section Break", "label": "Decision Matrix"},
        "bid_probability_score", "decision_matrix",

        # --- TAB 2 ---
        {"name": "tab_proposal", "type": "Tab Break", "label": "Proposal & Pricing"},
        
        {"name": "sec_finance", "type": "Section Break", "label": "Financials"},
        "estimated_cost", "margin_percentage", "final_bid_price", "payment_terms",
        
        {"name": "sec_strategy", "type": "Section Break", "label": "Strategy"},
        "win_themes", "client_pain_points",
        
        {"name": "sec_boq", "type": "Section Break", "label": "BOQ"},
        "items",

        # --- TAB 3 ---
        {"name": "tab_compliance", "type": "Tab Break", "label": "Compliance"},
        
        {"name": "sec_comp", "type": "Section Break", "label": "Competition"},
        "competitors",
        
        {"name": "sec_docs", "type": "Section Break", "label": "Documents & Review"},
        "required_documents", "loss_reason", "debrief_notes"
    ]

    # 3. BUILD THE FINAL LIST WITH SEQUENTIAL INDEXING
    final_fields = []
    current_idx = 1

    for item in target_order:
        new_field = None
        
        # Case A: It's a Layout Break (Dict)
        if isinstance(item, dict):
            new_field = frappe.new_doc("DocField")
            new_field.fieldname = item["name"]
            new_field.fieldtype = item["type"]
            new_field.label = item["label"]
        
        # Case B: It's a Data Field (String)
        elif isinstance(item, str):
            if item in field_repo:
                new_field = field_repo[item]
            else:
                # Fallback if field was deleted
                print(f"   ! Warning: Field '{item}' not found in repo, skipping.")
                continue

        # ASSIGN THE INDEX AND ADD
        if new_field:
            new_field.idx = current_idx
            final_fields.append(new_field)
            current_idx += 1

    # 4. OVERWRITE AND SAVE
    doc.fields = final_fields
    doc.save(ignore_permissions=True)
    
    print(f"--- ✅ RE-INDEXED {len(final_fields)} FIELDS ---")

if __name__ == "__main__":
    run()

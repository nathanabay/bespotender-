import frappe

def run():
    print("--- 🚚 MOVING 'GO/NO-GO' SECTION TO 'PROPOSAL & COSTING' ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. IDENTIFY ALL FIELDS IN THE GO/NO-GO GROUP
    # We need to grab the section header and every field belonging to it
    fields_to_move = [
        "sec_go_no_go",            # Section Header
        "bid_probability_score",   # Score
        "col_break_risk",          # Column Break (Risk)
        "technical_risk",
        "commercial_risk",
        "financial_risk",
        "sec_strategy_fit",        # Section (Strategy)
        "customer_relationship",
        "incumbent_vendor",
        "competition_level",
        "col_break_approver",      # Column Break (Approver)
        "decision_approver",
        "decision_date",
        "decision_matrix",         # Table
        "decision_notes"           # Notes
    ]
    
    # 2. CAPTURE FIELD OBJECTS
    field_map = {f.fieldname: f for f in doc.fields}
    
    # 3. REBUILD THE LAYOUT
    new_fields_list = []
    
    # Target: We will place it at the TOP of the "Proposal & Costing" tab
    target_tab = "tab_proposal" 
    
    for f in doc.fields:
        # A. Skip if it's one of the fields we are moving (removes from old spot)
        if f.fieldname in fields_to_move:
            continue
            
        # B. Add the current field
        new_fields_list.append(f)
        
        # C. Inject our group right after the Proposal Tab starts
        if f.fieldname == target_tab:
            print(f"   > Found '{target_tab}'. Injecting Go/No-Go Section...")
            for fname in fields_to_move:
                if fname in field_map:
                    new_fields_list.append(field_map[fname])
                    print(f"     + Moved: {fname}")
                else:
                    print(f"     ⚠ Missing field: {fname} (Skipping)")

    # 4. SAVE
    doc.fields = new_fields_list
    doc.save(ignore_permissions=True)
    print("--- ✅ GO/NO-GO SECTION MOVED ---")

if __name__ == "__main__":
    run()

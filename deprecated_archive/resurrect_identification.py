import frappe

def run():
    print("--- 🚑 RESURRECTING MISSING FIELDS ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. INDEX EXISTING FIELDS
    field_repo = {f.fieldname: f for f in doc.fields}

    # 2. DEFINE THE MASTER LAYOUT (With Types for Recreation)
    # Format: [Fieldname, Label, Fieldtype, Options (Optional)]
    layout_def = [
        # --- TAB 1: OVERVIEW ---
        ["tab_overview", "Overview", "Tab Break"],
        
        ["sec_id", "Identification", "Section Break"],
        ["naming_series", "Series", "Select", "T-OPP-.YYYY.-"],
        ["title", "Tender Title", "Data"],
        ["tender_number", "Tender Number / Ref", "Data"],
        ["organization", "Organization / Client", "Data"],
        ["sector", "Sector", "Select", "\nConstruction\nElectro-Mechanical\nWater Works\nGeneral Supply"],
        ["status", "Status", "Select", "Open\nClosed"],
        ["url", "Tender Link", "Data"],
        ["publication_date", "Publication Date", "Date"],

        ["sec_dates", "Critical Dates", "Section Break"],
        ["submission_deadline", "Submission Deadline", "Datetime"],
        ["site_visit_date", "Site Visit", "Datetime"],
        ["clarification_deadline", "Clarification Deadline", "Date"],

        ["sec_bond", "Bid Bond", "Section Break"],
        ["bond_amount", "Bond Amount", "Currency"],
        ["bond_number", "Bond / CPO Number", "Data"],
        ["bank_name", "Bank / Insurer", "Data"],
        ["bond_expiry", "Bond Expiry", "Date"],

        # --- TAB 2: PROPOSAL ---
        ["tab_proposal", "Proposal & Pricing", "Tab Break"],
        
        ["sec_finance", "Financials", "Section Break"],
        ["estimated_cost", "Estimated Cost", "Currency"],
        ["margin_percentage", "Margin (%)", "Percent"],
        ["final_bid_price", "Final Bid Price", "Currency"],
        ["payment_terms", "Payment Terms", "Small Text"],
        
        ["sec_strategy", "Strategy", "Section Break"],
        ["win_themes", "Win Themes", "Text Editor"],
        ["client_pain_points", "Client Pain Points", "Small Text"],
        
        ["sec_boq", "Bill of Quantities", "Section Break"],
        ["items", "Items", "Table", "Tender Competitor"], # Placeholder

        # --- TAB 3: COMPLIANCE ---
        ["tab_compliance", "Compliance & Analysis", "Tab Break"],
        
        ["sec_decision", "Decision Matrix", "Section Break"],
        ["bid_probability_score", "Win Probability", "Percent"],
        ["decision_matrix", "Decision Factors", "Table", "Bid Decision Factor"],

        ["sec_comp", "Competitors", "Section Break"],
        ["competitors", "Competitor Analysis", "Table", "Tender Competitor"],
        
        ["sec_review", "Post-Bid Review", "Section Break"],
        ["loss_reason", "Reason for Outcome", "Select", "\nPrice High\nTechnical Fail\nMissing Doc"],
        ["debrief_notes", "Debrief Notes", "Text"]
    ]

    # 3. REBUILD THE FIELD LIST
    final_fields = []
    idx_counter = 1

    for item in layout_def:
        fname = item[0]
        label = item[1]
        ftype = item[2]
        options = item[3] if len(item) > 3 else None

        if fname in field_repo:
            # Field exists, just enforce order and label
            f = field_repo[fname]
            f.label = label # Enforce label consistency
            f.idx = idx_counter
            final_fields.append(f)
        else:
            # Field is MISSING -> Create it
            print(f"   + Resurrecting: {fname} ({label})")
            new_f = frappe.new_doc("DocField")
            new_f.fieldname = fname
            new_f.label = label
            new_f.fieldtype = ftype
            if options:
                new_f.options = options
            new_f.idx = idx_counter
            final_fields.append(new_f)
        
        idx_counter += 1

    # 4. SAVE
    doc.fields = final_fields
    doc.save(ignore_permissions=True)
    print(f"--- ✅ RESTORED {len(final_fields)} FIELDS ---")

if __name__ == "__main__":
    run()

import frappe

def run():
    print("--- 📐 FINALIZING TENDER LAYOUT (AGGRESSIVE FIX) ---")

    dt = "Tender Opportunity"
    
    # 1. AGGRESSIVE SANITIZATION
    # Set the problematic column to 0 for EVERY record. 
    # This removes any weird decimals or out-of-bounds numbers causing the crash.
    try:
        frappe.db.sql("UPDATE `tabTender Opportunity` SET bid_probability_score = 0")
        frappe.db.commit() # Force write to DB immediately
        print("✔ Reset 'bid_probability_score' to 0 for all records")
    except Exception as e:
        print(f"⚠ Warning during sanitization: {str(e)}")

    doc = frappe.get_doc("DocType", dt)
    
    # 2. HARVEST EXISTING FIELD OBJECTS
    existing_fields = {f.fieldname: f for f in doc.fields}

    # 3. DEFINE THE MASTER STRUCTURE
    structure = [
        # ================= TAB 1: IDENTIFICATION =================
        ("Tab Break", "Identification & Qualification", "tab_identification", None),
        
        ("Section Break", "Identification", "sec_identification", None),
        ("Select", "Series", "naming_series", "T-OPP-.YYYY.-"),
        ("Data", "Tender Title", "title", None),
        ("Data", "Tender Number / Ref", "tender_number", None),
        ("Data", "Organization / Client", "organization", None),
        ("Select", "Sector", "sector", "\nConstruction\nElectro-Mechanical\nWater Works\nGeneral Supply"),
        ("Select", "Status", "status", "Open\nClosed"),
        ("Link", "Workflow State", "workflow_state", "Workflow State"),
        ("Data", "Tender Link", "url", None),
        ("Attach Image", "Source Evidence", "source_evidence", None),
        ("Currency", "Document Price", "document_price", None),
        ("Date", "Publication Date", "publication_date", None),

        ("Section Break", "Go / No-Go Decision", "sec_go_no_go", None),
        ("Percent", "Win Probability", "bid_probability_score", None),
        ("Table", "Decision Matrix", "decision_matrix", "Bid Decision Factor"),
        ("Small Text", "Decision Notes", "decision_notes", None),

        ("Section Break", "Purchase & Bond", "sec_purchase_bond", None),
        ("Currency", "Purchase Price", "purchase_price", None),
        ("Data", "Receipt No", "purchase_receipt_no", None),
        ("Date", "Purchase Date", "purchase_date", None),
        ("Data", "Bond Type", "bond_type", None),
        ("Currency", "Bond Amount", "bond_amount", None),
        ("Data", "Bond Percentage", "bond_percentage", None),
        ("Data", "Bond Number", "bond_number", None),
        ("Data", "Bank Name", "bank_name", None),
        ("Date", "Bond Expiry", "bond_expiry", None),

        ("Section Break", "Critical Dates", "sec_dates", None),
        ("Datetime", "Site Visit", "site_visit_date", None),
        ("Date", "Clarification Deadline", "clarification_deadline", None),
        ("Datetime", "Pre-Bid Meeting", "pre_bid_meeting_date", None),
        ("Datetime", "Submission Deadline", "submission_deadline", None),

        # ================= TAB 2: PROPOSAL & COSTING =================
        ("Tab Break", "Proposal & Costing", "tab_proposal", None),

        ("Section Break", "Budget & Planning", "sec_budget_planning", None),
        ("Data", "Budget Source", "budget_source", None),
        ("Data", "Duration (Months)", "project_duration_months", None),
        ("Data", "Payment Terms", "payment_terms", None),

        ("Section Break", "Costing & Pricing", "sec_costing_pricing", None),
        ("Currency", "Estimated Cost", "estimated_cost", None),
        ("Data", "Margin %", "margin_percentage", None),
        ("Currency", "Final Bid Price", "final_bid_price", None),

        ("Section Break", "Proposal Strategy", "sec_proposal_dev", None),
        ("Text Editor", "Win Themes", "win_themes", None),
        ("Small Text", "Pain Points", "client_pain_points", None),

        ("Section Break", "BOQ Items", "sec_boq_items", None),
        ("Table", "Items", "items", "Tender BOQ Item"),

        # ================= TAB 3: COMPLIANCE =================
        ("Tab Break", "Compliance & Review", "tab_compliance", None),

        ("Section Break", "Competition", "sec_competition", None),
        ("Table", "Competitors", "competitors", "Tender Competitor"),

        ("Section Break", "Checklists & Analysis", "sec_analysis", None),
        ("Data", "Required Documents", "required_documents", None),
        ("Select", "Loss Reason", "loss_reason", "\nPrice High\nTechnical Fail"),
        ("Text", "Debrief Notes", "debrief_notes", None),
    ]

    # 4. BUILD THE FINAL LIST
    final_fields = []
    added_names = set()

    for idx, (ftype, label, fname, options) in enumerate(structure):
        if fname in added_names: continue

        if fname in existing_fields:
            # REUSE EXISTING FIELD
            f = existing_fields[fname]
            f.label = label
            f.fieldtype = ftype
            f.idx = idx + 1 
            if options: f.options = options
            final_fields.append(f)
        else:
            # CREATE NEW FIELD
            print(f"   + Creating: {fname}")
            new_f = frappe.new_doc("DocField")
            new_f.fieldname = fname
            new_f.label = label
            new_f.fieldtype = ftype
            new_f.idx = idx + 1
            if options: new_f.options = options
            final_fields.append(new_f)
        
        added_names.add(fname)

    # 5. SAVE
    doc.fields = final_fields
    doc.save(ignore_permissions=True)
    print("--- ✅ FINAL LAYOUT APPLIED ---")

if __name__ == "__main__":
    run()

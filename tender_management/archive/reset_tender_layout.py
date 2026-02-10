import frappe

def run():
    print("--- 📐 PERFORMING FULL LAYOUT RESET ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. EXTRACT DATA FIELDS (Preserve their settings)
    # We ignore existing Tab/Section breaks because we will rebuild them fresh
    data_fields = {}
    for f in doc.fields:
        if f.fieldtype not in ["Tab Break", "Section Break", "Column Break"]:
            data_fields[f.fieldname] = f

    # Helper to create a NEW break field
    def create_break(fieldtype, label, fieldname):
        return frappe.new_doc("DocField", {
            "fieldtype": fieldtype,
            "label": label,
            "fieldname": fieldname
        })

    # 2. DEFINE THE MASTER SEQUENCE
    new_fields = []

    # ================= TAB 1: IDENTIFICATION (Must be first!) =================
    new_fields.append(create_break("Tab Break", "Identification & Qualification", "tab_identification"))
    
    new_fields.append(create_break("Section Break", "Identification", "sec_identification"))
    for f in ["title", "naming_series", "tender_number", "organization", "sector", "status", "workflow_state", "url", "publication_date"]:
        if f in data_fields: new_fields.append(data_fields[f])

    new_fields.append(create_break("Section Break", "Go / No-Go Decision", "sec_go_no_go"))
    for f in ["bid_probability_score", "decision_matrix", "decision_notes"]:
        if f in data_fields: new_fields.append(data_fields[f])

    new_fields.append(create_break("Section Break", "Purchase & Bond", "sec_purchase_bond"))
    for f in ["purchase_price", "purchase_receipt_no", "purchase_date", "bond_type", "bond_amount", "bond_percentage", "bond_number", "bank_name", "bond_expiry"]:
        if f in data_fields: new_fields.append(data_fields[f])

    new_fields.append(create_break("Section Break", "Dates", "sec_dates"))
    for f in ["site_visit_date", "pre_bid_meeting_date", "clarification_deadline"]:
        if f in data_fields: new_fields.append(data_fields[f])

    # ================= TAB 2: PROPOSAL & COSTING =================
    new_fields.append(create_break("Tab Break", "Proposal & Costing", "tab_proposal"))

    new_fields.append(create_break("Section Break", "Budget & Planning", "sec_budget_planning"))
    for f in ["budget_source", "project_duration_months", "payment_terms"]:
        if f in data_fields: new_fields.append(data_fields[f])

    new_fields.append(create_break("Section Break", "Costing & Pricing", "sec_costing_pricing"))
    for f in ["estimated_cost", "margin_percentage", "final_bid_price"]:
        if f in data_fields: new_fields.append(data_fields[f])

    new_fields.append(create_break("Section Break", "Proposal Development", "sec_proposal_dev"))
    for f in ["win_themes", "client_pain_points"]:
        if f in data_fields: new_fields.append(data_fields[f])

    new_fields.append(create_break("Section Break", "BOQ Items", "sec_boq_items"))
    for f in ["items"]:
        if f in data_fields: new_fields.append(data_fields[f])

    # ================= TAB 3: COMPLIANCE & REVIEW =================
    new_fields.append(create_break("Tab Break", "Compliance & Review", "tab_compliance"))

    new_fields.append(create_break("Section Break", "Competition", "sec_competition"))
    for f in ["competitors"]:
        if f in data_fields: new_fields.append(data_fields[f])

    new_fields.append(create_break("Section Break", "Checklists & Analysis", "sec_analysis"))
    for f in ["required_documents", "loss_reason", "debrief_notes"]:
        if f in data_fields: new_fields.append(data_fields[f])

    # 3. APPLY UPDATE
    doc.fields = new_fields
    doc.save(ignore_permissions=True)
    print("--- ✅ LAYOUT RESET COMPLETE ---")

if __name__ == "__main__":
    run()

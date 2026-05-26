import frappe

def run():
    print("--- 🧼 DEEP SCRUBBING TENDER LAYOUT ---")

    dt = "Tender Opportunity"
    
    # 1. DELETE GHOST SETTINGS (The "Customize Form" Overlay)
    # This removes any saved view preferences that conflict with our new structure
    frappe.db.sql("DELETE FROM `tabProperty Setter` WHERE doc_type = %s", (dt,))
    frappe.db.sql("DELETE FROM `tabCustom Field` WHERE dt = %s", (dt,))
    print("✔ Cleared Property Setters & Custom Field Overlays")

    # 2. GET DOCTYPE
    doc = frappe.get_doc("DocType", dt)
    
    # 3. MAP EXISTING FIELDS TO SAVE DATA
    # We grab the field objects so we don't lose the link to the data column
    field_map = {}
    for f in doc.fields:
        # We exclude structural elements because we want to create fresh clean ones
        if f.fieldtype not in ["Tab Break", "Section Break", "Column Break"]:
            field_map[f.fieldname] = f

    # 4. HELPER TO CREATE NEW STRUCTURES
    def make_field(fieldtype, label, fieldname, options=None):
        new_f = frappe.new_doc("DocField")
        new_f.fieldtype = fieldtype
        new_f.label = label
        new_f.fieldname = fieldname
        if options: new_f.options = options
        return new_f

    # 5. BUILD THE STRICT LAYOUT
    final_fields = []

    # --- TAB 1: IDENTIFICATION ---
    final_fields.append(make_field("Tab Break", "Identification & Qualification", "tab_identification"))
    
    final_fields.append(make_field("Section Break", "Identification", "sec_identification"))
    for f in ["title", "naming_series", "tender_number", "organization", "sector", "status", "workflow_state", "url", "publication_date"]:
        if f in field_map: final_fields.append(field_map[f])

    final_fields.append(make_field("Section Break", "Go / No-Go Decision", "sec_go_no_go"))
    for f in ["bid_probability_score", "decision_matrix", "decision_notes"]:
        if f in field_map: final_fields.append(field_map[f])

    final_fields.append(make_field("Section Break", "Purchase & Bond", "sec_purchase_bond"))
    for f in ["purchase_price", "purchase_receipt_no", "purchase_date", "bond_type", "bond_amount", "bond_percentage", "bond_number", "bank_name", "bond_expiry"]:
        if f in field_map: final_fields.append(field_map[f])
    
    final_fields.append(make_field("Section Break", "Dates", "sec_dates"))
    for f in ["site_visit_date", "pre_bid_meeting_date", "clarification_deadline"]:
        if f in field_map: final_fields.append(field_map[f])

    # --- TAB 2: PROPOSAL & COSTING (CORRECT SEQUENCE) ---
    final_fields.append(make_field("Tab Break", "Proposal & Costing", "tab_proposal"))

    final_fields.append(make_field("Section Break", "Budget & Planning", "sec_budget_planning"))
    for f in ["budget_source", "project_duration_months", "payment_terms"]:
        if f in field_map: final_fields.append(field_map[f])

    final_fields.append(make_field("Section Break", "Costing & Pricing", "sec_costing_pricing"))
    for f in ["estimated_cost", "margin_percentage", "final_bid_price"]:
        if f in field_map: final_fields.append(field_map[f])

    final_fields.append(make_field("Section Break", "Proposal Development", "sec_proposal_dev"))
    for f in ["win_themes", "client_pain_points"]:
        if f in field_map: final_fields.append(field_map[f])

    final_fields.append(make_field("Section Break", "BOQ Items", "sec_boq_items"))
    for f in ["items"]:
        if f in field_map: final_fields.append(field_map[f])

    # --- TAB 3: COMPLIANCE ---
    final_fields.append(make_field("Tab Break", "Compliance & Review", "tab_compliance"))

    final_fields.append(make_field("Section Break", "Competition", "sec_competition"))
    for f in ["competitors"]:
        if f in field_map: final_fields.append(field_map[f])

    final_fields.append(make_field("Section Break", "Checklists & Analysis", "sec_analysis"))
    for f in ["required_documents", "loss_reason", "debrief_notes"]:
        if f in field_map: final_fields.append(field_map[f])

    # 6. SAVE AND COMMIT
    doc.fields = final_fields
    doc.save(ignore_permissions=True)
    
    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ LAYOUT SCRUBBED & RESTORED ---")

if __name__ == "__main__":
    run()

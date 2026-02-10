import frappe

def run():
    print("--- 🔨 FORCING TABS TO INDEX 0 ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. IDENTIFY THE TAB FIELDS
    # We look for the fields we created earlier
    tab_id = "tab_identification"
    tab_prop = "tab_proposal" 
    tab_comp = "tab_compliance"

    # 2. SEPARATE FIELDS
    # We extract the specific tab fields from the list so we can re-insert them exactly where we want
    other_fields = []
    tabs = {}
    
    for f in doc.fields:
        if f.fieldname in [tab_id, tab_prop, tab_comp]:
            tabs[f.fieldname] = f
        else:
            other_fields.append(f)

    # 3. RECREATE MISSING TABS (Safety Net)
    # If the previous script failed to save them, we recreate them now
    if tab_id not in tabs:
        tabs[tab_id] = frappe.new_doc("DocField", {"fieldname": tab_id, "fieldtype": "Tab Break", "label": "Identification"})
    if tab_prop not in tabs:
        tabs[tab_prop] = frappe.new_doc("DocField", {"fieldname": tab_prop, "fieldtype": "Tab Break", "label": "Proposal & Costing"})
    if tab_comp not in tabs:
        tabs[tab_comp] = frappe.new_doc("DocField", {"fieldname": tab_comp, "fieldtype": "Tab Break", "label": "Compliance"})

    # 4. REBUILD THE LIST WITH STRICT ORDER
    final_fields = []
    
    # --- POS 1: MUST BE TAB BREAK ---
    final_fields.append(tabs[tab_id]) 
    
    # Add fields until we hit the next tab zone
    # We simply iterate through the 'other_fields' and split them based on Sections logic? 
    # To be safer/simpler, we assume the previous script ordered the DATA fields correctly, 
    # we just need to inject the TABS at the right intervals.
    
    # Since we can't easily know where the user wants the split in a generic list,
    # We will use the 'Section Break' fieldnames to guide us if they exist.
    
    # STRATEGY: We rebuild the layout explicitly again. This is the only way to guarantee the order.
    
    # Map of all available fields for quick lookup
    f_map = {f.fieldname: f for f in other_fields}
    
    # A. Tab 1 Content
    final_fields.append(f_map.get("sec_identification") or frappe.new_doc("DocField", {"fieldtype": "Section Break", "label": "Identification"}))
    for x in ["title", "naming_series", "tender_number", "organization", "sector", "status", "workflow_state", "url", "publication_date"]:
        if x in f_map: final_fields.append(f_map[x])

    final_fields.append(f_map.get("sec_go_no_go") or frappe.new_doc("DocField", {"fieldtype": "Section Break", "label": "Go/No-Go"}))
    for x in ["bid_probability_score", "decision_matrix", "decision_notes"]:
        if x in f_map: final_fields.append(f_map[x])

    final_fields.append(f_map.get("sec_purchase_bond") or frappe.new_doc("DocField", {"fieldtype": "Section Break", "label": "Purchase"}))
    for x in ["purchase_price", "purchase_receipt_no", "purchase_date", "bond_type", "bond_amount", "bond_percentage", "bond_number", "bank_name", "bond_expiry"]:
        if x in f_map: final_fields.append(f_map[x])
        
    final_fields.append(f_map.get("sec_dates") or frappe.new_doc("DocField", {"fieldtype": "Section Break", "label": "Dates"}))
    for x in ["site_visit_date", "pre_bid_meeting_date", "clarification_deadline"]:
        if x in f_map: final_fields.append(f_map[x])

    # B. Tab 2 Content
    final_fields.append(tabs[tab_prop])
    
    final_fields.append(f_map.get("sec_budget_planning") or frappe.new_doc("DocField", {"fieldtype": "Section Break", "label": "Planning"}))
    for x in ["budget_source", "project_duration_months", "payment_terms"]:
        if x in f_map: final_fields.append(f_map[x])

    final_fields.append(f_map.get("sec_costing_pricing") or frappe.new_doc("DocField", {"fieldtype": "Section Break", "label": "Costing"}))
    for x in ["estimated_cost", "margin_percentage", "final_bid_price"]:
        if x in f_map: final_fields.append(f_map[x])

    final_fields.append(f_map.get("sec_proposal_dev") or frappe.new_doc("DocField", {"fieldtype": "Section Break", "label": "Strategy"}))
    for x in ["win_themes", "client_pain_points"]:
        if x in f_map: final_fields.append(f_map[x])

    final_fields.append(f_map.get("sec_boq_items") or frappe.new_doc("DocField", {"fieldtype": "Section Break", "label": "BOQ"}))
    for x in ["items"]:
        if x in f_map: final_fields.append(f_map[x])

    # C. Tab 3 Content
    final_fields.append(tabs[tab_comp])
    
    final_fields.append(f_map.get("sec_competition") or frappe.new_doc("DocField", {"fieldtype": "Section Break", "label": "Competition"}))
    for x in ["competitors"]:
        if x in f_map: final_fields.append(f_map[x])

    final_fields.append(f_map.get("sec_analysis") or frappe.new_doc("DocField", {"fieldtype": "Section Break", "label": "Analysis"}))
    for x in ["required_documents", "loss_reason", "debrief_notes"]:
        if x in f_map: final_fields.append(f_map[x])

    # 5. SAVE
    doc.fields = final_fields
    doc.save(ignore_permissions=True)
    print("--- ✅ TABS ARE NOW INDEX 0 ---")

if __name__ == "__main__":
    run()

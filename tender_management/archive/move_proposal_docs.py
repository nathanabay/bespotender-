import frappe

def run():
    print("--- 🚚 MOVING PROPOSAL DOCUMENTS TO 'PROPOSAL & COSTING' TAB ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. IDENTIFY FIELDS TO MOVE
    fields_to_move = [
        "sec_proposal_docs",      # The Section Header
        "quotation_ref",          # Linked Quotation
        "technical_proposal",     # Tech Upload
        "financial_proposal_doc"  # Fin Upload
    ]
    
    # 2. CAPTURE FIELD OBJECTS
    field_map = {f.fieldname: f for f in doc.fields}
    
    # Check if they exist before moving
    for fname in fields_to_move:
        if fname not in field_map:
            print(f"⚠ Warning: Field '{fname}' not found. It might have been deleted.")
            # If critical fields are missing, recreate them on the fly
            if fname == "sec_proposal_docs":
                new_f = frappe.new_doc("DocField")
                new_f.label = "Proposal Documents"
                new_f.fieldtype = "Section Break"
                new_f.fieldname = fname
                field_map[fname] = new_f
            elif fname == "quotation_ref":
                new_f = frappe.new_doc("DocField")
                new_f.label = "Linked Quotation"
                new_f.fieldtype = "Link"
                new_f.options = "Quotation"
                new_f.fieldname = fname
                field_map[fname] = new_f
            elif fname == "technical_proposal":
                 new_f = frappe.new_doc("DocField")
                 new_f.label = "Technical Proposal"
                 new_f.fieldtype = "Attach"
                 new_f.fieldname = fname
                 field_map[fname] = new_f
            elif fname == "financial_proposal_doc":
                 new_f = frappe.new_doc("DocField")
                 new_f.label = "Financial Proposal (File)"
                 new_f.fieldtype = "Attach"
                 new_f.fieldname = fname
                 field_map[fname] = new_f

    # 3. REBUILD THE LAYOUT
    new_fields_list = []
    
    # We will insert our moved fields *right after* this tab starts
    target_tab = "tab_proposal" 
    
    for f in doc.fields:
        # A. If this is one of the fields we want to move, SKIP it (it gets removed from old spot)
        if f.fieldname in fields_to_move:
            continue
            
        # B. Add the current field to the new list
        new_fields_list.append(f)
        
        # C. If we just added the Target Tab, inject our moved fields immediately after
        if f.fieldname == target_tab:
            print(f"   > Found '{target_tab}'. Injecting documents...")
            for fname in fields_to_move:
                if fname in field_map:
                    new_fields_list.append(field_map[fname])
                    print(f"     + Moved: {fname}")

    # 4. SAVE
    doc.fields = new_fields_list
    doc.save(ignore_permissions=True)
    print("--- ✅ FIELDS MOVED SUCCESSFULLY ---")

if __name__ == "__main__":
    run()

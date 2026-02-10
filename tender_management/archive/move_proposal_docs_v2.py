import frappe

def run():
    print("--- 🚚 MOVING PROPOSAL DOCUMENTS TO 'PROPOSAL & COSTING' TAB ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. IDENTIFY FIELDS TO MOVE
    # These are the fields currently in the wrong tab
    fields_to_move = [
        "sec_proposal_docs",      # Section Header
        "quotation_ref",          # Linked Quotation
        "technical_proposal",     # Technical Upload
        "financial_proposal_doc"  # Financial Upload
    ]
    
    # 2. CAPTURE FIELD OBJECTS
    # We grab the actual field definitions so we preserve their settings
    field_map = {f.fieldname: f for f in doc.fields}
    
    # 3. REBUILD THE LAYOUT
    new_fields_list = []
    
    # The target location: The start of the "Proposal & Costing" tab
    target_tab = "tab_proposal" 
    
    fields_moved = False

    for f in doc.fields:
        # A. If this is one of the fields we want to move, SKIP it now (it gets removed from old spot)
        if f.fieldname in fields_to_move:
            continue
            
        # B. Add the current field to the new list
        new_fields_list.append(f)
        
        # C. Check if we just added the Target Tab
        if f.fieldname == target_tab:
            print(f"   > Found '{target_tab}'. Injecting documents section here...")
            
            # Inject our specific fields in order
            for fname in fields_to_move:
                if fname in field_map:
                    new_fields_list.append(field_map[fname])
                    print(f"     + Moved: {fname}")
                else:
                    # Safety net: Recreate if somehow missing
                    print(f"     + Creating missing: {fname}")
                    new_f = frappe.new_doc("DocField")
                    new_f.fieldname = fname
                    
                    if fname == "sec_proposal_docs":
                        new_f.label = "Proposal Documents"
                        new_f.fieldtype = "Section Break"
                    elif fname == "quotation_ref":
                        new_f.label = "Linked Quotation"
                        new_f.fieldtype = "Link"
                        new_f.options = "Quotation"
                    elif fname == "technical_proposal":
                        new_f.label = "Technical Proposal"
                        new_f.fieldtype = "Attach"
                    elif fname == "financial_proposal_doc":
                        new_f.label = "Financial Proposal (File)"
                        new_f.fieldtype = "Attach"
                    
                    new_fields_list.append(new_f)

            fields_moved = True

    # 4. SAVE
    doc.fields = new_fields_list
    doc.save(ignore_permissions=True)
    print("--- ✅ FIELDS SUCCESSFULLY MOVED ---")

if __name__ == "__main__":
    run()

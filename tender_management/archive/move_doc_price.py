import frappe

def run():
    print("--- 🚚 MOVING DOCUMENT PRICE TO IDENTIFICATION ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. CAPTURE EXISTING FIELDS
    field_map = {f.fieldname: f for f in doc.fields}
    
    # 2. DEFINE THE STRICT ORDER FOR IDENTIFICATION SECTION
    # This guarantees 'document_price' appears here.
    id_section_target = [
        "sec_identification", 
        "naming_series", 
        "title", 
        "tender_number", 
        "organization", 
        "sector", 
        "status", 
        "workflow_state", 
        "url", 
        "source_evidence", 
        "document_price", # <--- TARGET LOCATION
        "publication_date"
    ]
    
    # 3. REBUILD THE LIST
    new_fields = []
    processed = set()
    
    # A. Inject the Identification Section FIRST
    # We look for the 'tab_identification' to place our section right after it.
    tab_found = False
    
    for f in doc.fields:
        # If we hit the Identification Tab, we dump our section immediately after
        if f.fieldname == "tab_identification":
            new_fields.append(f)
            
            # Now dump the ID section fields
            for fname in id_section_target:
                if fname in field_map:
                    new_fields.append(field_map[fname])
                else:
                    # Create if missing
                    print(f"   + Creating missing: {fname}")
                    nf = frappe.new_doc("DocField")
                    nf.fieldname = fname
                    nf.label = fname.replace("_", " ").title()
                    nf.fieldtype = "Currency" if "price" in fname else "Data"
                    new_fields.append(nf)
                
                processed.add(fname) # Mark as handled
            
            tab_found = True
            continue
            
        # If the field is one we already placed in the ID section, SKIP it (Move operation)
        if f.fieldname in processed:
            continue
            
        # Add all other fields (Proposal tab, Compliance tab, other sections)
        new_fields.append(f)
        
    # B. Safety Net: If Tab wasn't found, insert at top
    if not tab_found:
        print("   ! Identification Tab not found, prepending section at top.")
        for fname in reversed(id_section_target):
             if fname in field_map:
                new_fields.insert(0, field_map[fname])

    # 4. SAVE
    doc.fields = new_fields
    doc.save(ignore_permissions=True)
    print("--- ✅ DOCUMENT PRICE MOVED ---")

if __name__ == "__main__":
    run()

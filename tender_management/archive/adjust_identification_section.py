import frappe

def run():
    print("--- 📑 UPDATING IDENTIFICATION SECTION ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. PREPARE THE FIELDS
    # We pull existing fields or create new ones if missing
    
    # Check/Create Document Price
    if not any(f.fieldname == "document_price" for f in doc.fields):
        new_price = frappe.new_doc("DocField")
        new_price.fieldname = "document_price"
        new_price.label = "Document Price"
        new_price.fieldtype = "Currency"
        new_price.insert_after = "source_evidence"
        print("   + Created new field: Document Price")
    
    # 2. DEFINE THE EXACT ORDER FOR "IDENTIFICATION" SECTION
    # This list defines exactly what should appear under the first section header
    id_section_order = [
        "sec_identification",   # The Section Header
        "naming_series",
        "title", 
        "tender_number", 
        "organization", 
        "sector", 
        "status", 
        "workflow_state", 
        "url", 
        "source_evidence",      # Moved Here
        "document_price",       # Added Here
        "publication_date"
    ]
    
    # 3. REBUILD THE FIELD LIST
    new_fields = []
    processed_fields = set(id_section_order) # Keep track of what we've handled
    
    # First, locate the Identification Section in the existing list and swap it with our perfect block
    id_section_inserted = False
    
    # We verify if fields exist in the doc before adding them to avoid errors
    existing_field_map = {f.fieldname: f for f in doc.fields}
    
    # Create the new list
    for f in doc.fields:
        # If we hit the Identification Section (or start of form), inject our block
        if f.fieldname == "sec_identification" and not id_section_inserted:
            for fname in id_section_order:
                if fname in existing_field_map:
                    new_fields.append(existing_field_map[fname])
                elif fname == "document_price":
                    # Create the object on the fly if it wasn't in the map
                    nf = frappe.new_doc("DocField")
                    nf.fieldname = "document_price"
                    nf.label = "Document Price (Advertised)"
                    nf.fieldtype = "Currency"
                    new_fields.append(nf)
            id_section_inserted = True
            continue
        
        # If this field is one of the ones we already placed in our block, SKIP it (don't duplicate)
        if f.fieldname in processed_fields:
            continue
            
        # Otherwise, keep the field where it is (preserve other tabs/sections)
        new_fields.append(f)

    # 4. SAVE
    doc.fields = new_fields
    doc.save(ignore_permissions=True)
    print("--- ✅ IDENTIFICATION SECTION UPDATED ---")

if __name__ == "__main__":
    run()

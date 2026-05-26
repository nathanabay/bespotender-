import frappe

def run():
    print("--- 📑 UPDATING IDENTIFICATION SECTION (FIXED) ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. SNAPSHOT EXISTING FIELDS
    field_map = {f.fieldname: f for f in doc.fields}
    
    # 2. DEFINE THE PERFECT IDENTIFICATION ORDER
    id_section_order = [
        "sec_identification",   # Header
        "naming_series",        # REQUIRED for ID generation
        "title", 
        "tender_number", 
        "organization", 
        "sector", 
        "status", 
        "workflow_state", 
        "url", 
        "source_evidence",      # Attachment
        "document_price",       # New Field
        "publication_date"
    ]
    
    # Set of fields we are manually placing (to avoid duplication later)
    placed_fields = set(id_section_order)

    # 3. HELPER: GET OR CREATE FIELD
    def get_field(fname):
        if fname in field_map:
            return field_map[fname]
        
        # If missing, create on the fly
        print(f"   + Re-creating missing field: {fname}")
        new_f = frappe.new_doc("DocField")
        new_f.fieldname = fname
        
        if fname == "naming_series":
            new_f.label = "Series"
            new_f.fieldtype = "Select"
            new_f.options = "T-OPP-.YYYY.-"
        elif fname == "document_price":
            new_f.label = "Document Price"
            new_f.fieldtype = "Currency"
        elif fname == "source_evidence":
            new_f.label = "Source Evidence"
            new_f.fieldtype = "Attach Image"
        elif fname == "sec_identification":
            new_f.label = "Identification"
            new_f.fieldtype = "Section Break"
        else:
            # Generic fallback
            new_f.label = fname.replace("_", " ").title()
            new_f.fieldtype = "Data"
            
        return new_f

    # 4. BUILD THE NEW FIELD LIST
    new_fields_list = []
    
    # A. Find the top of the form (Tabs usually come first)
    # We will inject the ID section specifically inside the "Identification" tab if possible,
    # or just at the top if we can't find it.
    
    id_injected = False
    
    for f in doc.fields:
        # If we hit the old Identification section, REPLACE it with our new block
        if f.fieldname == "sec_identification":
            if not id_injected:
                for target_field in id_section_order:
                    new_fields_list.append(get_field(target_field))
                id_injected = True
            continue # Skip the old section header
            
        # If the field is one of the ones we just placed, skip it (don't duplicate)
        if f.fieldname in placed_fields:
            continue
            
        # Keep everything else (Tabs, other sections, etc.)
        new_fields_list.append(f)

    # Safety Fallback: If sec_identification wasn't found to replace, put it at the top (after Tab 1)
    if not id_injected:
        print("   > Injecting Identification Section at top")
        # Insert after the first field (usually Tab 1)
        insert_pos = 1 if len(new_fields_list) > 0 else 0
        for target_field in reversed(id_section_order):
            new_fields_list.insert(insert_pos, get_field(target_field))

    # 5. SAVE
    doc.fields = new_fields_list
    doc.save(ignore_permissions=True)
    print("--- ✅ IDENTIFICATION SECTION UPDATED ---")

if __name__ == "__main__":
    run()

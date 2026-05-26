import frappe

def run():
    print("--- 📎 ADDING SOURCE EVIDENCE ATTACHMENT FIELD ---")
    
    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # Check if field already exists to prevent duplicates
    if any(f.fieldname == "source_evidence" for f in doc.fields):
        print("✔ Field 'source_evidence' already exists.")
        return

    # Create the new field object
    new_field = frappe.new_doc("DocField")
    new_field.fieldname = "source_evidence"
    new_field.label = "Source Evidence (Clipping/Screenshot)"
    new_field.fieldtype = "Attach Image" # Shows a preview thumbnail
    new_field.description = "Attach a photo of the newspaper ad or screenshot of the website."
    
    # Insert it intelligently after the 'Tender Link' (url) field
    new_fields_list = []
    inserted = False
    
    for f in doc.fields:
        new_fields_list.append(f)
        if f.fieldname == "url" and not inserted:
            new_fields_list.append(new_field)
            inserted = True
            print("   > Inserting after 'url'")
            
    # Fallback: If 'url' isn't found, put it in the Identification section
    if not inserted:
        for i, f in enumerate(new_fields_list):
            if f.fieldname == "sec_identification":
                new_fields_list.insert(i+5, new_field) # Insert a few rows down
                inserted = True
                print("   > Inserting into Identification Section")
                break

    doc.fields = new_fields_list
    doc.save(ignore_permissions=True)
    
    print("--- ✅ EVIDENCE FIELD ADDED ---")

if __name__ == "__main__":
    run()

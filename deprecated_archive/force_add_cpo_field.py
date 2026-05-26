import frappe

def run():
    print("--- 🩹 FORCING 'CPO JOURNAL ENTRY' FIELD VISIBILITY ---")

    dt = "Tender Opportunity"
    fname = "cpo_journal_entry"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. CHECK IF FIELD EXISTS IN LIST
    exists = False
    for f in doc.fields:
        if f.fieldname == fname:
            exists = True
            print("✔ Field already exists in DocType list.")
            break
            
    # 2. CREATE IF MISSING
    if not exists:
        new_field = frappe.new_doc("DocField")
        new_field.fieldname = fname
        new_field.label = "CPO Journal Entry"
        new_field.fieldtype = "Link"
        new_field.options = "Journal Entry"
        new_field.description = "Link the accounting entry that froze these funds."
        
        # INSERT STRATEGY: Find 'bond_amount' and put it 2 slots down
        insert_index = -1
        for i, f in enumerate(doc.fields):
            if f.fieldname == "bond_amount":
                insert_index = i + 2 # After amount and percentage
                break
        
        if insert_index > -1:
            doc.fields.insert(insert_index, new_field)
            print(f"   + Inserted field after 'bond_amount' (Index {insert_index})")
        else:
            # Fallback: Append to end of first section
            doc.fields.append(new_field)
            print("   + Appended field to end (Fallback)")
            
        doc.save(ignore_permissions=True)
        print("✔ DocType Saved with New Field")

    # 3. FORCE DB SCHEMA SYNC
    # Sometimes metadata is saved but DB column isn't created
    if not frappe.db.has_column(dt, fname):
        print("... Syncing Database Schema")
        frappe.model.sync.sync(dt) 

    # 4. CLEAR CACHE (Crucial)
    frappe.clear_cache(doctype=dt)
    print("--- ✅ REPAIR COMPLETE: RELOAD BROWSER ---")

if __name__ == "__main__":
    run()

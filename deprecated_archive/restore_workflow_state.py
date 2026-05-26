import frappe

def run():
    print("--- 🚑 RESTORING MISSING 'WORKFLOW_STATE' FIELD ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # Check if it already exists (to avoid duplicates)
    exists = any(f.fieldname == "workflow_state" for f in doc.fields)
    
    if not exists:
        # Create the field
        wf_field = frappe.new_doc("DocField")
        wf_field.fieldname = "workflow_state"
        wf_field.label = "Workflow State"
        wf_field.fieldtype = "Link"
        wf_field.options = "Workflow State"
        wf_field.read_only = 1 # Should be controlled by workflow engine
        
        # Insert it right after 'Status'
        new_fields = []
        for f in doc.fields:
            new_fields.append(f)
            if f.fieldname == "status":
                new_fields.append(wf_field)
                print("✔ Inserted 'Workflow State' field after 'Status'")
        
        doc.fields = new_fields
        doc.save(ignore_permissions=True)
        print("--- ✅ REPAIR COMPLETE ---")
    else:
        print("--- ℹ️ Field already exists (No action taken) ---")

if __name__ == "__main__":
    run()

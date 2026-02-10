import frappe

def run():
    print("--- 📂 ADDING PROPOSAL DOCUMENTS & QUOTATION LINK ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. DEFINE NEW FIELDS
    # We create the objects first
    new_fields_map = {
        "sec_proposal_docs": frappe.new_doc("DocField", {
            "fieldname": "sec_proposal_docs",
            "label": "Proposal Documents",
            "fieldtype": "Section Break"
        }),
        "technical_proposal": frappe.new_doc("DocField", {
            "fieldname": "technical_proposal",
            "label": "Technical Proposal",
            "fieldtype": "Attach",
            "description": "Upload the full technical proposal (PDF/Doc)"
        }),
        "financial_proposal_doc": frappe.new_doc("DocField", {
            "fieldname": "financial_proposal_doc",
            "label": "Financial Proposal (File)",
            "fieldtype": "Attach",
            "description": "Upload the BOQ or Financial Offer"
        }),
        "quotation_ref": frappe.new_doc("DocField", {
            "fieldname": "quotation_ref",
            "label": "Linked Quotation",
            "fieldtype": "Link",
            "options": "Quotation",
            "description": "Link a Quotation from the Selling Module"
        })
    }

    # 2. INJECT FIELDS INTO LAYOUT
    # We iterate through the list and insert our new section right after the "Proposal & Costing" tab start
    
    final_fields = []
    inserted = False
    
    for f in doc.fields:
        final_fields.append(f)
        
        # Look for the Tab Start
        if f.fieldname == "tab_proposal" and not inserted:
            print("   > Found 'Proposal' Tab, injecting documents section...")
            
            # Add Section Header
            final_fields.append(new_fields_map["sec_proposal_docs"])
            
            # Add Data Fields
            final_fields.append(new_fields_map["technical_proposal"])
            final_fields.append(new_fields_map["financial_proposal_doc"])
            final_fields.append(new_fields_map["quotation_ref"])
            
            inserted = True

    # 3. SAVE
    if inserted:
        doc.fields = final_fields
        doc.save(ignore_permissions=True)
        print("--- ✅ DOCUMENTS SECTION ADDED ---")
    else:
        print("--- ⚠ Could not find 'tab_proposal'. Check layout. ---")

if __name__ == "__main__":
    run()

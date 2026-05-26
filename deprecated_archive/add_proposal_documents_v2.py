import frappe

def run():
    print("--- 📂 ADDING PROPOSAL DOCUMENTS & QUOTATION LINK (FIXED) ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. HELPER TO CREATE FIELDS PROPERLY
    def create_field(label, fieldname, fieldtype, options=None, description=None):
        df = frappe.new_doc("DocField")
        df.label = label
        df.fieldname = fieldname
        df.fieldtype = fieldtype
        if options: df.options = options
        if description: df.description = description
        return df

    # 2. DEFINE THE NEW FIELDS
    new_fields_batch = [
        create_field("Proposal Documents", "sec_proposal_docs", "Section Break"),
        create_field("Technical Proposal", "technical_proposal", "Attach", description="Upload the full technical proposal (PDF/Doc)"),
        create_field("Financial Proposal (File)", "financial_proposal_doc", "Attach", description="Upload the BOQ or Financial Offer"),
        create_field("Linked Quotation", "quotation_ref", "Link", options="Quotation", description="Link a Quotation from the Selling Module")
    ]

    # 3. INJECT INTO LAYOUT
    final_fields = []
    inserted = False
    existing_names = [f.fieldname for f in doc.fields]
    
    for f in doc.fields:
        final_fields.append(f)
        
        # Inject immediately after the Proposal Tab starts
        if f.fieldname == "tab_proposal" and not inserted:
            print("   > Found 'Proposal' Tab. Injecting new section...")
            
            for nf in new_fields_batch:
                # Prevent duplicates if running multiple times
                if nf.fieldname not in existing_names:
                    final_fields.append(nf)
                    print(f"     + Added: {nf.label}")
                else:
                    print(f"     . Skipped (Exists): {nf.label}")
            
            inserted = True

    # 4. SAVE
    if inserted:
        doc.fields = final_fields
        doc.save(ignore_permissions=True)
        print("--- ✅ DOCUMENTS SECTION ADDED SUCCESSFULLY ---")
    else:
        print("--- ⚠ Error: Could not find 'tab_proposal' in layout. ---")

if __name__ == "__main__":
    run()

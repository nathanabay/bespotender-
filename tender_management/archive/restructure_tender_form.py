import frappe

def run():
    print("--- 📑 REORGANIZING TENDER OPPORTUNITY FORM ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. HARVEST EXISTING FIELDS (Preserve their definitions)
    # We store all existing fields in a dictionary so we don't lose settings
    field_map = {f.fieldname: f for f in doc.fields}
    
    # 2. DEFINE THE NEW LAYOUT STRUCTURE
    # We define the ideal order of Tabs > Sections > Fields
    layout_plan = [
        # ================= TAB 1: IDENTIFICATION & QUALIFICATION =================
        {"type": "Tab Break", "label": "Identification & Qualification"},
        
        {"type": "Section Break", "label": "Identification (Scraper)"},
        "title", "naming_series", "tender_number", "organization", "sector", "status", "workflow_state", "url", "publication_date",
        
        {"type": "Section Break", "label": "Go / No-Go Decision (Internal)"},
        "bid_probability_score", "decision_matrix", "decision_notes", # Existing matrix fields
        
        {"type": "Section Break", "label": "Tender Purchase Details"},
        "purchase_price", "purchase_receipt_no", "purchase_date", # Will create if missing
        
        {"type": "Section Break", "label": "Bid Bond Details"},
        "bond_type", "bond_amount", "bond_percentage", "bond_number", "bank_name", "bond_expiry",
        
        {"type": "Section Break", "label": "Document Acquisition"},
        "site_visit_date", "pre_bid_meeting_date", "clarification_deadline", # Will create if missing

        # ================= TAB 2: PROPOSAL & COSTING =================
        {"type": "Tab Break", "label": "Proposal & Costing"},
        
        {"type": "Section Break", "label": "Budget & Planning"},
        "budget_source", "project_duration_months", "payment_terms", # Will create
        
        {"type": "Section Break", "label": "Proposal Strategy"},
        "win_themes", "client_pain_points", # Existing fields from previous step
        
        {"type": "Section Break", "label": "Costing & Pricing"},
        "estimated_cost", "margin_percentage", "final_bid_price",
        
        {"type": "Section Break", "label": "BOQ & Items"},
        "items", # Assuming standard Item table or we create a BOQ table

        # ================= TAB 3: COMPLIANCE & REVIEW =================
        {"type": "Tab Break", "label": "Compliance & Review"},
        
        {"type": "Section Break", "label": "Scoring Matrix & Competitors"},
        "competitors", # Existing competitor table
        
        {"type": "Section Break", "label": "Document Checklist"},
        "required_documents", # Will create checklist table
        
        {"type": "Section Break", "label": "Post-Bid Analysis"},
        "loss_reason", "debrief_notes"
    ]

    # 3. REBUILD THE FIELD LIST
    new_fields = []
    
    for item in layout_plan:
        # If it's a structural element (Tab/Section), create a new row
        if isinstance(item, dict):
            new_row = frappe.new_doc("DocField")
            new_row.update(item)
            new_fields.append(new_row)
        
        # If it's a field name, pull the existing field OR create a placeholder if missing
        elif isinstance(item, str):
            fieldname = item
            if fieldname in field_map:
                new_fields.append(field_map[fieldname])
                del field_map[fieldname] # Mark as moved
            else:
                # FIELD DOES NOT EXIST - AUTO CREATE IT
                # We infer type based on name keywords
                ft = "Data"
                if "date" in fieldname: ft = "Date"
                elif "price" in fieldname or "amount" in fieldname or "cost" in fieldname: ft = "Currency"
                elif "no" in fieldname: ft = "Data"
                elif "notes" in fieldname: ft = "Small Text"
                elif "check" in fieldname or "items" in fieldname: ft = "Table"
                
                print(f"   + Creating missing field: {fieldname} ({ft})")
                
                new_row = frappe.new_doc("DocField")
                new_row.fieldname = fieldname
                new_row.label = fieldname.replace("_", " ").title()
                new_row.fieldtype = ft
                if ft == "Table": new_row.options = "Tender Competitor" # Default fallback, user can change
                
                new_fields.append(new_row)

    # 4. APPEND LEFTOVERS (Any custom fields we didn't explicitly place)
    # We put them in a "More Info" section at the end so they aren't lost
    if field_map:
        new_fields.append(frappe.new_doc("DocField", {"fieldtype": "Tab Break", "label": "Other Details"}))
        for fname, fdoc in field_map.items():
            if fdoc.fieldtype not in ["Tab Break", "Section Break", "Column Break"]:
                new_fields.append(fdoc)

    # 5. SAVE
    doc.fields = new_fields
    doc.save(ignore_permissions=True)
    print("--- ✅ FORM RESTRUCTURED SUCCESSFULLY ---")

if __name__ == "__main__":
    run()

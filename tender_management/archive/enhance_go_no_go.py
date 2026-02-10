import frappe

def run():
    print("--- 🧠 ENHANCING GO / NO-GO DECISION MATRIX ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. HELPER TO CREATE FIELDS
    def create_field(label, fieldname, fieldtype, options=None, reqd=0):
        df = frappe.new_doc("DocField")
        df.label = label
        df.fieldname = fieldname
        df.fieldtype = fieldtype
        if options: df.options = options
        df.reqd = reqd
        return df

    # 2. DEFINE NEW FIELDS
    new_fields_map = {
        # Risk Assessment
        "col_break_risk": create_field("Risk Column", "col_break_risk", "Column Break"),
        "technical_risk": create_field("Technical Risk", "technical_risk", "Select", "Low\nMedium\nHigh"),
        "commercial_risk": create_field("Commercial Risk", "commercial_risk", "Select", "Low\nMedium\nHigh"),
        "financial_risk": create_field("Financial Risk", "financial_risk", "Select", "Low\nMedium\nHigh"),
        
        # Strategic Position
        "sec_strategy_fit": create_field("Strategic Fit", "sec_strategy_fit", "Section Break"),
        "customer_relationship": create_field("Customer Relationship", "customer_relationship", "Select", "New Client\nExisting - Good\nExisting - Strained\nBlacklisted"),
        "incumbent_vendor": create_field("Incumbent Vendor?", "incumbent_vendor", "Data"),
        "competition_level": create_field("Competition Level", "competition_level", "Select", "Low\nModerate\nIntense\nLocked Spec"),
        
        # Approval
        "col_break_approver": create_field("Approval Column", "col_break_approver", "Column Break"),
        "decision_approver": create_field("Decision Approver", "decision_approver", "Link", "User"),
        "decision_date": create_field("Decision Date", "decision_date", "Date")
    }

    # 3. INJECT INTO LAYOUT
    final_fields = []
    inserted = False
    existing_names = [f.fieldname for f in doc.fields]

    for f in doc.fields:
        final_fields.append(f)
        
        # We inject right after the 'bid_probability_score' to keep it grouped
        if f.fieldname == "bid_probability_score" and not inserted:
            print("   > Found 'Go/No-Go' Section. Injecting details...")
            
            # Add Risk Column
            if "col_break_risk" not in existing_names: final_fields.append(new_fields_map["col_break_risk"])
            if "technical_risk" not in existing_names: final_fields.append(new_fields_map["technical_risk"])
            if "commercial_risk" not in existing_names: final_fields.append(new_fields_map["commercial_risk"])
            if "financial_risk" not in existing_names: final_fields.append(new_fields_map["financial_risk"])

            # Add Strategy Section
            if "sec_strategy_fit" not in existing_names: final_fields.append(new_fields_map["sec_strategy_fit"])
            if "customer_relationship" not in existing_names: final_fields.append(new_fields_map["customer_relationship"])
            if "incumbent_vendor" not in existing_names: final_fields.append(new_fields_map["incumbent_vendor"])
            
            # Add Approver Column
            if "col_break_approver" not in existing_names: final_fields.append(new_fields_map["col_break_approver"])
            if "competition_level" not in existing_names: final_fields.append(new_fields_map["competition_level"])
            if "decision_approver" not in existing_names: final_fields.append(new_fields_map["decision_approver"])
            if "decision_date" not in existing_names: final_fields.append(new_fields_map["decision_date"])
            
            inserted = True

    # 4. SAVE
    if inserted:
        doc.fields = final_fields
        doc.save(ignore_permissions=True)
        print("--- ✅ GO/NO-GO DETAILS ADDED ---")
    else:
        print("⚠ Could not find 'bid_probability_score' to anchor fields.")

if __name__ == "__main__":
    run()

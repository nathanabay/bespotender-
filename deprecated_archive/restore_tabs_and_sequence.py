import frappe

def run():
    print("--- 🛠️ RESTORING TABS & FIXING SEQUENCE ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. INDEX EXISTING FIELDS
    # We map fieldnames to their objects so we can reuse them (preserving IDs)
    fields = {f.fieldname: f for f in doc.fields}
    
    # Helper to get or create a structural field (Tab/Section)
    def get_structure(fieldname, label, fieldtype):
        if fieldname in fields:
            f = fields[fieldname]
            f.label = label # Update label if changed
            f.fieldtype = fieldtype
            return f
        else:
            return frappe.new_doc("DocField", {
                "fieldname": fieldname,
                "label": label,
                "fieldtype": fieldtype
            })

    # 2. DEFINE THE STRICT SEQUENCE
    # We explicitly list the fieldname objects in order
    new_sequence = []

    # --- TAB 1: IDENTIFICATION ---
    new_sequence.append(get_structure("tab_identification", "Identification & Qualification", "Tab Break"))
    
    new_sequence.append(get_structure("sec_identification", "Identification", "Section Break"))
    new_sequence.extend([fields.get(f) for f in ["title", "naming_series", "tender_number", "organization", "sector", "status", "workflow_state", "url", "publication_date"] if f in fields])

    new_sequence.append(get_structure("sec_go_no_go", "Go / No-Go Decision", "Section Break"))
    new_sequence.extend([fields.get(f) for f in ["bid_probability_score", "decision_matrix", "decision_notes"] if f in fields])

    new_sequence.append(get_structure("sec_purchase_bond", "Purchase & Bond", "Section Break"))
    new_sequence.extend([fields.get(f) for f in ["purchase_price", "purchase_receipt_no", "purchase_date", "bond_type", "bond_amount", "bond_percentage", "bond_number", "bank_name", "bond_expiry"] if f in fields])

    new_sequence.append(get_structure("sec_dates", "Dates", "Section Break"))
    new_sequence.extend([fields.get(f) for f in ["site_visit_date", "pre_bid_meeting_date", "clarification_deadline"] if f in fields])

    # --- TAB 2: PROPOSAL & COSTING (YOUR REQUESTED ORDER) ---
    new_sequence.append(get_structure("tab_proposal", "Proposal & Costing", "Tab Break"))

    new_sequence.append(get_structure("sec_budget_planning", "Budget & Planning", "Section Break"))
    new_sequence.extend([fields.get(f) for f in ["budget_source", "project_duration_months", "payment_terms"] if f in fields])

    new_sequence.append(get_structure("sec_costing_pricing", "Costing & Pricing", "Section Break"))
    new_sequence.extend([fields.get(f) for f in ["estimated_cost", "margin_percentage", "final_bid_price"] if f in fields])

    new_sequence.append(get_structure("sec_proposal_dev", "Proposal Development", "Section Break"))
    new_sequence.extend([fields.get(f) for f in ["win_themes", "client_pain_points"] if f in fields])

    new_sequence.append(get_structure("sec_boq_items", "BOQ Items", "Section Break"))
    new_sequence.extend([fields.get(f) for f in ["items"] if f in fields])

    # --- TAB 3: COMPLIANCE ---
    new_sequence.append(get_structure("tab_compliance", "Compliance & Review", "Tab Break"))

    new_sequence.append(get_structure("sec_competition", "Competition", "Section Break"))
    new_sequence.extend([fields.get(f) for f in ["competitors"] if f in fields])

    new_sequence.append(get_structure("sec_analysis", "Checklists & Analysis", "Section Break"))
    new_sequence.extend([fields.get(f) for f in ["required_documents", "loss_reason", "debrief_notes"] if f in fields])

    # 3. APPLY AND SAVE
    # Remove None values (in case a field was missing)
    doc.fields = [f for f in new_sequence if f]
    
    doc.save(ignore_permissions=True)
    print("--- ✅ TABS RESTORED & SEQUENCE FIXED ---")

if __name__ == "__main__":
    run()

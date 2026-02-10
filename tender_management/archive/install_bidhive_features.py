import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def run():
    print("--- 🚀 INSTALLING BIDHIVE FEATURES ---")

    # ==============================================================================
    # 1. CREATE CHILD TABLE: "Tender Competitor"
    # To track who we are bidding against and their prices
    # ==============================================================================
    if not frappe.db.exists("DocType", "Tender Competitor"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Tender Competitor",
            "module": "Tender Management",
            "istable": 1,
            "editable_grid": 1,
            "fields": [
                {"label": "Competitor Name", "fieldname": "competitor_name", "fieldtype": "Data", "in_list_view": 1, "reqd": 1},
                {"label": "Their Bid Price", "fieldname": "bid_price", "fieldtype": "Currency", "in_list_view": 1},
                {"label": "Strengths/Weaknesses", "fieldname": "notes", "fieldtype": "Small Text"},
                {"label": "Winner?", "fieldname": "is_winner", "fieldtype": "Check", "in_list_view": 1}
            ]
        })
        doc.insert(ignore_permissions=True)
        print("✔ Created Child Table: Tender Competitor")

    # ==============================================================================
    # 2. CREATE CHILD TABLE: "Bid Decision Factor"
    # To calculate the Win Probability Score (Bid/No-Bid)
    # ==============================================================================
    if not frappe.db.exists("DocType", "Bid Decision Factor"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Bid Decision Factor",
            "module": "Tender Management",
            "istable": 1,
            "editable_grid": 1,
            "fields": [
                {"label": "Decision Factor", "fieldname": "factor", "fieldtype": "Data", "in_list_view": 1, "reqd": 1},
                {"label": "Score (0-5)", "fieldname": "score", "fieldtype": "Int", "in_list_view": 1, "reqd": 1, "default": 3},
                {"label": "Weight (%)", "fieldname": "weight", "fieldtype": "Percent", "in_list_view": 1, "default": 20}
            ]
        })
        doc.insert(ignore_permissions=True)
        print("✔ Created Child Table: Bid Decision Factor")

    # ==============================================================================
    # 3. INJECT FIELDS INTO "TENDER OPPORTUNITY"
    # Adding the Strategy, Competitor, and Analysis sections
    # ==============================================================================
    
    # Check if Tab Break exists, if not, we append at the end
    fields_to_add = [
        # --- TAB: BID STRATEGY (The Capture Plan) ---
        {"fieldname": "sb_strategy", "fieldtype": "Tab Break", "label": "Bid Strategy (Capture Plan)"},
        
        {"fieldname": "win_themes", "fieldtype": "Text Editor", "label": "Our Win Themes (Why us?)", "description": "Key selling points to emphasize in the proposal."},
        {"fieldname": "client_pain_points", "fieldtype": "Small Text", "label": "Client Pain Points", "description": "What keeps the client awake at night?"},
        
        {"fieldname": "sec_decision", "fieldtype": "Section Break", "label": "Bid/No-Bid Decision"},
        {"fieldname": "bid_probability_score", "fieldtype": "Percent", "label": "Win Probability Score", "read_only": 1, "description": "Calculated based on decision factors."},
        {"fieldname": "decision_matrix", "fieldtype": "Table", "label": "Decision Matrix", "options": "Bid Decision Factor"},

        # --- TAB: COMPETITIVE INTEL ---
        {"fieldname": "sb_competitors", "fieldtype": "Tab Break", "label": "Competitors"},
        {"fieldname": "competitors", "fieldtype": "Table", "label": "Competitor Analysis", "options": "Tender Competitor"},

        # --- TAB: POST-BID ANALYSIS ---
        {"fieldname": "sb_analysis", "fieldtype": "Tab Break", "label": "Post-Bid Analysis"},
        {"fieldname": "loss_reason", "fieldtype": "Select", "label": "Reason for Outcome", "options": "\nPrice High\nPrice Low (Left Money on Table)\nTechnical Non-Compliance\nMissing Documents\nClient Relationship\nCompetitor Strength\nStrategic Withdrawal"},
        {"fieldname": "debrief_notes", "fieldtype": "Text", "label": "Debrief / Lessons Learned"}
    ]

    create_custom_fields({
        "Tender Opportunity": fields_to_add
    })
    print("✔ Injected Strategy & Analysis Fields")

    # ==============================================================================
    # 4. ADD DEFAULT "BID/NO-BID" LOGIC
    # We add a script to auto-calculate the score when you save
    # ==============================================================================
    # Logic: Sum(Score * Weight) / Sum(Weights) * 20 (to get percentage out of 100)
    
    script_name = "Calculate Bid Score"
    if frappe.db.exists("Server Script", script_name):
        frappe.delete_doc("Server Script", script_name)

    script_content = """
total_score = 0
total_weight = 0

for row in doc.decision_matrix:
    total_score += (row.score * row.weight)
    total_weight += row.weight

if total_weight > 0:
    # Normalize: Max score is 5. So (Total / Total Weight) gives avg score 0-5.
    # Divide by 5 then * 100 to get %.
    # Simplified: (Sum(Score*Weight) / TotalWeight) * 20
    doc.bid_probability_score = (total_score / total_weight) * 20
"""
    
    frappe.get_doc({
        "doctype": "Server Script",
        "name": script_name,
        "script_type": "DocType Event",
        "reference_doctype": "Tender Opportunity",
        "doctype_event": "Before Save",
        "script": script_content
    }).insert(ignore_permissions=True)
    print("✔ Added Auto-Calculation Logic for Bid Score")

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ BIDHIVE UPGRADE COMPLETE ---")

if __name__ == "__main__":
    run()

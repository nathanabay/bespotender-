import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def run():
    print("--- 🚀 IMPLEMENTING RESPONSIVE.IO FEATURES ---")

    # ==============================================================================
    # 1. CONTENT LIBRARY (The "Knowledge Base")
    # ==============================================================================
    # Stores reusable answers (CVs, Certs, Technical Specs) to speed up bidding.
    if not frappe.db.exists("DocType", "Tender Content Library"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "module": "Tender Management",
            "name": "Tender Content Library",
            "custom": 1,
            "fields": [
                {"label": "Topic / Question", "fieldname": "topic", "fieldtype": "Data", "reqd": 1, "in_list_view": 1},
                {"label": "Category", "fieldname": "category", "fieldtype": "Select", "options": "Company Info\nTechnical Spec\nFinancial\nLegal\nSafety", "in_list_view": 1},
                {"label": "Approved Answer", "fieldname": "answer", "fieldtype": "Text Editor", "reqd": 1},
                {"label": "Keywords (Tags)", "fieldname": "tags", "fieldtype": "Data"},
                {"label": "Last Updated", "fieldname": "last_updated", "fieldtype": "Date", "default": "Today"},
                {"label": "Owner (SME)", "fieldname": "sme_owner", "fieldtype": "Link", "options": "User"}
            ]
        })
        doc.insert(ignore_permissions=True)
        print("✔ Created Feature: Content Library (Knowledge Base)")

    # ==============================================================================
    # 2. COMPETITOR INTELLIGENCE (Child Table)
    # ==============================================================================
    # Tracks who you are bidding against.
    if not frappe.db.exists("DocType", "Tender Competitor"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "module": "Tender Management",
            "name": "Tender Competitor",
            "istable": 1,
            "custom": 1,
            "fields": [
                {"label": "Competitor Name", "fieldname": "competitor", "fieldtype": "Data", "in_list_view": 1},
                {"label": "Perceived Strength", "fieldname": "strength", "fieldtype": "Select", "options": "Price\nTechnical\nRelationship\nNone"},
                {"label": "Our Advantage", "fieldname": "advantage", "fieldtype": "Data"},
                {"label": "Estimated Bid Price", "fieldname": "est_price", "fieldtype": "Currency"}
            ]
        })
        doc.insert(ignore_permissions=True)
        print("✔ Created Feature: Competitor Intelligence")

    # ==============================================================================
    # 3. RFP REQUIREMENT BREAKDOWN (Child Table)
    # ==============================================================================
    # Allows "Shredding" the RFP into assignable tasks.
    if not frappe.db.exists("DocType", "Tender Requirement"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "module": "Tender Management",
            "name": "Tender Requirement",
            "istable": 1,
            "custom": 1,
            "fields": [
                {"label": "Requirement / Question", "fieldname": "requirement", "fieldtype": "Text", "reqd": 1, "in_list_view": 1},
                {"label": "Assigned SME", "fieldname": "assigned_to", "fieldtype": "Link", "options": "User", "in_list_view": 1},
                {"label": "Status", "fieldname": "status", "fieldtype": "Select", "options": "Pending\nDrafted\nReviewed", "default": "Pending"},
                {"label": "Response Source", "fieldname": "source_content", "fieldtype": "Link", "options": "Tender Content Library", "label": "Use Library Content"}
            ]
        })
        doc.insert(ignore_permissions=True)
        print("✔ Created Feature: Requirements Matrix")

    # ==============================================================================
    # 4. UPGRADE MAIN TENDER DOCTYPE
    # ==============================================================================
    # Integrate these new features into the main screen.
    fields = {
        "Tender Opportunity": [
            # A. Go/No-Go Decision Matrix
            {"fieldname": "sb_qualify", "label": "1. Qualification (Go/No-Go)", "fieldtype": "Section Break", "insert_after": "sector"},
            {"fieldname": "win_probability", "label": "Win Probability (%)", "fieldtype": "Percent", "insert_after": "sb_qualify"},
            {"fieldname": "strategic_value", "label": "Strategic Value", "fieldtype": "Select", "options": "High\nMedium\nLow", "insert_after": "win_probability"},
            {"fieldname": "capability_match", "label": "Capability Match", "fieldtype": "Select", "options": "Full\nPartial\nLow", "insert_after": "strategic_value"},
            
            # B. Requirements Section
            {"fieldname": "sb_requirements", "label": "2. Requirements & Response", "fieldtype": "Section Break", "insert_after": "capability_match"},
            {"fieldname": "requirements_matrix", "label": "RFP Breakdown (Shredder)", "fieldtype": "Table", "options": "Tender Requirement", "insert_after": "sb_requirements"},
            
            # C. Competitor Section
            {"fieldname": "sb_comp", "label": "3. Market Intelligence", "fieldtype": "Section Break", "insert_after": "requirements_matrix"},
            {"fieldname": "competitors", "label": "Known Competitors", "fieldtype": "Table", "options": "Tender Competitor", "insert_after": "sb_comp"}
        ]
    }
    create_custom_fields(fields)
    
    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ RESPONSIVE FEATURES ACTIVE ---")

if __name__ == "__main__":
    run()

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def run():
    print("--- 🚀 STARTING ENTERPRISE UPGRADE ---")

    # ==============================================================================
    # 1. CREATE CHILD TABLES (For Scoring & Checklists)
    # ==============================================================================
    
    # A. Evaluation Criteria (Feature 4 - Scoring)
    if not frappe.db.exists("DocType", "Tender Evaluation Criteria"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "module": "Tender Management",
            "name": "Tender Evaluation Criteria",
            "istable": 1,
            "custom": 1,
            "fields": [
                {"label": "Criteria", "fieldname": "criteria", "fieldtype": "Data", "reqd": 1, "in_list_view": 1},
                {"label": "Weight (%)", "fieldname": "weight", "fieldtype": "Percent", "reqd": 1, "in_list_view": 1},
                {"label": "Max Score", "fieldname": "max_score", "fieldtype": "Int", "default": "10"}
            ]
        })
        doc.insert(ignore_permissions=True)
        print("✔ Created Child Table: Evaluation Criteria")

    # B. Document Checklist (Feature 5 - Compliance)
    if not frappe.db.exists("DocType", "Tender Document Checklist"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "module": "Tender Management",
            "name": "Tender Document Checklist",
            "istable": 1,
            "custom": 1,
            "fields": [
                {"label": "Document Name", "fieldname": "document_name", "fieldtype": "Data", "reqd": 1, "in_list_view": 1},
                {"label": "Mandatory?", "fieldname": "is_mandatory", "fieldtype": "Check", "default": "1"},
                {"label": "Uploaded?", "fieldname": "is_uploaded", "fieldtype": "Check", "read_only": 1}
            ]
        })
        doc.insert(ignore_permissions=True)
        print("✔ Created Child Table: Document Checklist")

    # ==============================================================================
    # 2. CREATE "TENDER BID" DOCTYPE (Feature 2 & 3 - Vendor Management)
    # ==============================================================================
    # This separates the "Opportunity" (Our Request) from the "Bid" (Vendor's Response)
    if not frappe.db.exists("DocType", "Tender Bid"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "module": "Tender Management",
            "name": "Tender Bid",
            "custom": 1,
            "is_submittable": 1,
            "autoname": "BID-.YYYY.-.#####",
            "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "submit": 1}],
            "fields": [
                {"label": "Tender Reference", "fieldname": "tender", "fieldtype": "Link", "options": "Tender Opportunity", "reqd": 1},
                {"label": "Supplier / Vendor", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "reqd": 1},
                {"label": "Quote Amount", "fieldname": "quote_amount", "fieldtype": "Currency", "reqd": 1},
                {"label": "Technical Score", "fieldname": "technical_score", "fieldtype": "Float"},
                {"label": "Submitted On", "fieldname": "submission_date", "fieldtype": "Date", "default": "Today"},
                {"label": "Status", "fieldname": "status", "fieldtype": "Select", "options": "Received\nEvaluated\nShortlisted\nRejected\nAwarded", "default": "Received"}
            ]
        })
        doc.insert(ignore_permissions=True)
        print("✔ Created DocType: Tender Bid (Vendor Submissions)")

    # ==============================================================================
    # 3. UPDATE TENDER OPPORTUNITY (Feature 9 - Cost & Budget)
    # ==============================================================================
    fields = {
        "Tender Opportunity": [
            # Feature 9: Budgeting
            {"fieldname": "sb_budget", "label": "9. Budget & Planning", "fieldtype": "Section Break", "insert_after": "workflow_state"},
            {"fieldname": "budget_allocated", "label": "Budget Allocated", "fieldtype": "Currency", "insert_after": "sb_budget"},
            {"fieldname": "estimated_cost", "label": "Estimated Cost", "fieldtype": "Currency", "insert_after": "budget_allocated"},
            {"fieldname": "budget_variance", "label": "Variance", "fieldtype": "Currency", "read_only": 1, "insert_after": "estimated_cost"},
            
            # Feature 4: Evaluation Setup
            {"fieldname": "sb_criteria", "label": "4. Evaluation Criteria", "fieldtype": "Section Break", "insert_after": "final_bid_price"},
            {"fieldname": "evaluation_criteria", "label": "Scoring Matrix", "fieldtype": "Table", "options": "Tender Evaluation Criteria", "insert_after": "sb_criteria"},
            
            # Feature 5: Compliance
            {"fieldname": "sb_docs", "label": "5. Required Documents", "fieldtype": "Section Break", "insert_after": "evaluation_criteria"},
            {"fieldname": "required_documents", "label": "Document Checklist", "fieldtype": "Table", "options": "Tender Document Checklist", "insert_after": "sb_docs"}
        ]
    }
    create_custom_fields(fields)
    print("✔ Added Enterprise Fields (Budget, Matrix, Checklist)")

    # ==============================================================================
    # 4. AUTOMATION: NOTIFICATION (Feature 6)
    # ==============================================================================
    if not frappe.db.exists("Notification", "Tender Deadline Alert"):
        doc = frappe.get_doc({
            "doctype": "Notification",
            "name": "Tender Deadline Alert",
            "subject": "Urgent: Tender Deadline Approaching",
            "document_type": "Tender Opportunity",
            "event": "Days Before",
            "days_in_advance": 2,
            "date_changed": "submission_deadline",
            "channel": "System Notification",
            "recipients": [{"receiver_by_document_field": "owner"}],
            "message": "The tender {{ title }} is closing in 2 days. Please ensure all bids are logged."
        })
        doc.insert(ignore_permissions=True)
        print("✔ Automation: Deadline Alerts Configured")

    # ==============================================================================
    # 5. SECURITY: AUDIT TRAIL (Feature 7)
    # ==============================================================================
    # Enable track changes on the main doctype
    frappe.make_property_setter({
        "doctype": "Tender Opportunity",
        "doctype_or_field": "DocType",
        "property": "track_changes",
        "value": 1
    })
    print("✔ Security: Audit Trail Enabled")

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ ENTERPRISE UPGRADE COMPLETE ---")

if __name__ == "__main__":
    run()

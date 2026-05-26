import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def run():
    print("--- 🩺 SANITIZING DATABASE & APPLYING ENTERPRISE UPGRADE ---")

    # ==============================================================================
    # 1. SURGICAL FIX: REMOVE DUPLICATE FIELDS
    # ==============================================================================
    dt = "Tender Opportunity"
    try:
        doc = frappe.get_doc("DocType", dt)
        
        seen_fields = set()
        fields_to_keep = []
        duplicates_removed = 0

        for field in doc.fields:
            # Check if we've seen this fieldname before
            if field.fieldname in seen_fields:
                print(f"   ✂️ Removing duplicate field: {field.fieldname}")
                duplicates_removed += 1
            else:
                seen_fields.add(field.fieldname)
                fields_to_keep.append(field)
        
        if duplicates_removed > 0:
            doc.fields = fields_to_keep
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"✔ Successfully removed {duplicates_removed} duplicate fields.")
        else:
            print("✔ DocType is clean (no duplicates found).")

    except Exception as e:
        print(f"⚠️ Warning during sanitization: {e}")

    # ==============================================================================
    # 2. CREATE CHILD TABLES (Scoring & Compliance)
    # ==============================================================================
    # A. Evaluation Criteria
    if not frappe.db.exists("DocType", "Tender Evaluation Criteria"):
        frappe.get_doc({
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
        }).insert(ignore_permissions=True)
        print("✔ Created Child Table: Evaluation Criteria")

    # B. Document Checklist
    if not frappe.db.exists("DocType", "Tender Document Checklist"):
        frappe.get_doc({
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
        }).insert(ignore_permissions=True)
        print("✔ Created Child Table: Document Checklist")

    # ==============================================================================
    # 3. CREATE "TENDER BID" DOCTYPE (Vendor Submissions)
    # ==============================================================================
    if not frappe.db.exists("DocType", "Tender Bid"):
        frappe.get_doc({
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
                {"label": "Status", "fieldname": "status", "fieldtype": "Select", "options": "Received\nEvaluated\nShortlisted\nRejected\nAwarded", "default": "Received"}
            ]
        }).insert(ignore_permissions=True)
        print("✔ Created DocType: Tender Bid")

    # ==============================================================================
    # 4. APPLY ENTERPRISE FIELDS
    # ==============================================================================
    fields = {
        "Tender Opportunity": [
            # Budgeting
            {"fieldname": "sb_budget", "label": "9. Budget & Planning", "fieldtype": "Section Break", "insert_after": "workflow_state"},
            {"fieldname": "budget_allocated", "label": "Budget Allocated", "fieldtype": "Currency", "insert_after": "sb_budget"},
            {"fieldname": "estimated_cost", "label": "Estimated Cost", "fieldtype": "Currency", "insert_after": "budget_allocated"},
            
            # Evaluation
            {"fieldname": "sb_criteria", "label": "4. Evaluation Criteria", "fieldtype": "Section Break", "insert_after": "final_bid_price"},
            {"fieldname": "evaluation_criteria", "label": "Scoring Matrix", "fieldtype": "Table", "options": "Tender Evaluation Criteria", "insert_after": "sb_criteria"},
            
            # Compliance
            {"fieldname": "sb_docs", "label": "5. Required Documents", "fieldtype": "Section Break", "insert_after": "evaluation_criteria"},
            {"fieldname": "required_documents", "label": "Document Checklist", "fieldtype": "Table", "options": "Tender Document Checklist", "insert_after": "sb_docs"}
        ]
    }
    
    create_custom_fields(fields)
    print("✔ Enterprise Fields Applied")

    # ==============================================================================
    # 5. AUTOMATION & SECURITY
    # ==============================================================================
    # Notification
    if not frappe.db.exists("Notification", "Tender Deadline Alert"):
        frappe.get_doc({
            "doctype": "Notification",
            "name": "Tender Deadline Alert",
            "subject": "Urgent: Tender Deadline",
            "document_type": "Tender Opportunity",
            "event": "Days Before",
            "days_in_advance": 2,
            "date_changed": "submission_deadline",
            "channel": "System Notification",
            "recipients": [{"receiver_by_document_field": "owner"}]
        }).insert(ignore_permissions=True)
        print("✔ Notification Configured")

    # Audit Trail
    frappe.make_property_setter({
        "doctype": "Tender Opportunity",
        "doctype_or_field": "DocType",
        "property": "track_changes",
        "value": 1
    })
    print("✔ Audit Trail Enabled")

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ ENTERPRISE UPGRADE SUCCESSFUL ---")

if __name__ == "__main__":
    run()

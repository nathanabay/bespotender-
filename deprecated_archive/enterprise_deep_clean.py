import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def run():
    print("--- 🩺 STARTING DEEP CLEAN & ENTERPRISE DEPLOY ---")

    dt = "Tender Opportunity"

    # ==============================================================================
    # 1. REMOVE CONFLICTING CUSTOM FIELDS (The "Double Vision" Fix)
    # ==============================================================================
    # If a field exists in the DocType AND in 'Custom Field', it causes UniqueFieldnameError.
    # We delete the Custom Field overlays for fields we know we are managing in the DocType.
    conflicting_fields = ["submission_deadline", "final_bid_price", "naming_series", "sector"]
    
    for field in conflicting_fields:
        if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": field}):
            frappe.db.delete("Custom Field", {"dt": dt, "fieldname": field})
            print(f"   ✂️ Removed conflicting Custom Field overlay: {field}")
    
    frappe.db.commit()

    # ==============================================================================
    # 2. SANITIZE DOCTYPE METADATA
    # ==============================================================================
    doc = frappe.get_doc("DocType", dt)
    
    # Rebuild the field list, keeping only the first instance of every fieldname
    unique_fields = []
    seen = set()
    
    for f in doc.fields:
        if f.fieldname not in seen:
            seen.add(f.fieldname)
            unique_fields.append(f)
        else:
            print(f"   ✂️ Pruning duplicate row in DocType: {f.fieldname}")

    doc.fields = unique_fields
    doc.save(ignore_permissions=True)
    print("✔ DocType Definition Sanitized")

    # ==============================================================================
    # 3. INSTALL CHILD TABLES
    # ==============================================================================
    # Evaluation Criteria
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
        print("✔ Child Table: Evaluation Criteria")

    # Document Checklist
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
        print("✔ Child Table: Document Checklist")

    # Tender Bid (Vendor Submissions)
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
        print("✔ DocType: Tender Bid")

    # ==============================================================================
    # 4. APPLY ENTERPRISE FIELDS
    # ==============================================================================
    # Now that the duplicates are gone, we can safely add the new sections
    enterprise_fields = {
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
    
    create_custom_fields(enterprise_fields)
    print("✔ Enterprise Fields Applied Successfully")

    # ==============================================================================
    # 5. CONFIGURE AUTOMATION
    # ==============================================================================
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

    frappe.db.commit()
    frappe.clear_cache()
    print("--- ✅ SUCCESS: ENTERPRISE FEATURES DEPLOYED ---")

if __name__ == "__main__":
    run()

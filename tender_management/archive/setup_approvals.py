import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def run():
    print("--- 🛡️ INSTALLING GO/NO-GO APPROVAL GATES ---")

    # 1. ADD APPROVAL FIELDS TO DOCTYPE
    # We add a specific section for the decision-makers.
    fields = {
        "Tender Opportunity": [
            {
                "fieldname": "sb_approvals",
                "label": "Go / No-Go Decision (Internal Use Only)",
                "fieldtype": "Section Break",
                "insert_after": "scan_preview" 
            },
            {
                "fieldname": "eng_approval",
                "label": "Engineering Decision",
                "fieldtype": "Select",
                "options": "Pending\nApproved\nRejected",
                "default": "Pending",
                "insert_after": "sb_approvals"
            },
            {
                "fieldname": "eng_approver",
                "label": "Engineering Approver",
                "fieldtype": "Link",
                "options": "User",
                "read_only": 1,
                "insert_after": "eng_approval"
            },
            {
                "fieldname": "fin_approval",
                "label": "Finance Decision",
                "fieldtype": "Select",
                "options": "Pending\nApproved\nRejected",
                "default": "Pending",
                "insert_after": "eng_approver"
            },
            {
                "fieldname": "fin_approver",
                "label": "Finance Approver",
                "fieldtype": "Link",
                "options": "User",
                "read_only": 1,
                "insert_after": "fin_approval"
            },
            {
                "fieldname": "col_break_app",
                "fieldtype": "Column Break",
                "insert_after": "fin_approver"
            },
            {
                "fieldname": "approval_remarks",
                "label": "Decision Remarks (Why?)",
                "fieldtype": "Small Text",
                "insert_after": "col_break_app"
            }
        ]
    }

    create_custom_fields(fields)
    print("✔ Added Approval Fields")

    # 2. CREATE VALIDATION SCRIPT (THE GATEKEEPER)
    # This Server Script prevents the workflow from proceeding if approvals are missing.
    
    script_name = "Tender Gatekeeper"
    if frappe.db.exists("Server Script", script_name):
        frappe.delete_doc("Server Script", script_name)

    # The Python Logic running on the server
    script_code = """
# 1. Check if user changed the Approval Status
if doc.eng_approval == "Approved" and doc.db_get("eng_approval") != "Approved":
    doc.eng_approver = frappe.session.user

if doc.fin_approval == "Approved" and doc.db_get("fin_approval") != "Approved":
    doc.fin_approver = frappe.session.user

# 2. DEFINE RESTRICTED STATES
# These are the stages that require approval to enter
restricted_states = ["To Buy", "Buying", "Scanning", "Proposal", "Review", "Approved"]

if doc.workflow_state in restricted_states:
    # 3. CHECK ENGINEERING
    if doc.eng_approval != "Approved":
        frappe.throw(f"⛔ <b>STOP:</b> You cannot proceed to '{doc.workflow_state}'.<br><br>The <b>Engineering Team</b> must approve this Tender first in the 'Go / No-Go' section.")

    # 4. CHECK FINANCE
    if doc.fin_approval != "Approved":
        frappe.throw(f"⛔ <b>STOP:</b> You cannot proceed to '{doc.workflow_state}'.<br><br>The <b>Financial Team</b> must approve this Tender first in the 'Go / No-Go' section.")
"""

    frappe.get_doc({
        "doctype": "Server Script",
        "name": script_name,
        "script_type": "DocType Event",
        "reference_doctype": "Tender Opportunity",
        "doctype_event": "Before Save",
        "script": script_code
    }).insert(ignore_permissions=True)
    
    print("✔ Installed Gatekeeper Logic")
    
    frappe.db.commit()
    print("--- ✅ APPROVAL SYSTEM ACTIVE ---")

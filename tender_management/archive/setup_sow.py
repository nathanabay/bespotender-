import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def run():
    print("--- 🏗 IMPLEMENTING TENDER SOW REQUIREMENTS ---")

    # ==============================================================================
    # 1. CREATE "BID SECURITY (CPO)" DOCTYPE (For Financial Control)
    # ==============================================================================
    if not frappe.db.exists("DocType", "Bid Security"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "module": "Tender Management",
            "name": "Bid Security",
            "custom": 1,
            "is_submittable": 0,
            "permissions": [{"role": "Accounts Manager", "read": 1, "write": 1, "create": 1}],
            "fields": [
                {"label": "Bank Name", "fieldname": "bank", "fieldtype": "Data", "reqd": 1, "in_list_view": 1},
                {"label": "CPO / Reference Number", "fieldname": "cpo_number", "fieldtype": "Data", "reqd": 1, "in_list_view": 1},
                {"label": "Amount (ETB)", "fieldname": "amount", "fieldtype": "Currency", "reqd": 1, "in_list_view": 1},
                {"label": "Linked Tender", "fieldname": "tender", "fieldtype": "Link", "options": "Tender Opportunity", "reqd": 1},
                {"label": "Expiry Date", "fieldname": "expiry_date", "fieldtype": "Date", "reqd": 1},
                {"label": "Status", "fieldname": "status", "fieldtype": "Select", "options": "Active\nReturned\nConfiscated\nExpired", "default": "Active"},
                {"label": "Return Date", "fieldname": "return_date", "fieldtype": "Date"},
                {"label": "Attachment (Scan)", "fieldname": "scan", "fieldtype": "Attach"}
            ]
        })
        doc.insert(ignore_permissions=True)
        print("✔ Created Doctype: 'Bid Security' (CPO Tracking)")

    # ==============================================================================
    # 2. CREATE BOQ CHILD TABLE (For Cost Estimation)
    # ==============================================================================
    if not frappe.db.exists("DocType", "Tender BOQ Item"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "module": "Tender Management",
            "name": "Tender BOQ Item",
            "istable": 1,
            "custom": 1,
            "fields": [
                {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "columns": 2},
                {"label": "Description", "fieldname": "description", "fieldtype": "Text Editor"},
                {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "columns": 1},
                {"label": "UOM", "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "columns": 1},
                {"label": "Estimated Cost", "fieldname": "cost_rate", "fieldtype": "Currency", "columns": 2},
                {"label": "Margin %", "fieldname": "margin_percent", "fieldtype": "Float", "default": "20", "columns": 1},
                {"label": "Bid Rate", "fieldname": "bid_rate", "fieldtype": "Currency", "read_only": 1, "columns": 2},
                {"label": "Total Bid Amount", "fieldname": "amount", "fieldtype": "Currency", "read_only": 1, "columns": 2}
            ]
        })
        doc.insert(ignore_permissions=True)
        print("✔ Created Child Table: 'Tender BOQ Item'")

    # ==============================================================================
    # 3. UPDATE "TENDER OPPORTUNITY" DOCTYPE (The Central Registry)
    # ==============================================================================
    # We update the existing doc to match the SOW exactly
    dt = "Tender Opportunity"
    
    # 3.1 New Fields for Header, Key Dates, and Financials
    fields_to_add = {
        dt: [
            # Header Info
            {"fieldname": "tender_number", "label": "Tender Number", "fieldtype": "Data", "insert_after": "title"},
            {"fieldname": "type", "label": "Type", "fieldtype": "Select", "options": "Open\nRestricted\nDirect Procurement", "insert_after": "client"},
            
            # Key Dates Section
            {"fieldname": "sb_dates", "label": "Key Deadlines", "fieldtype": "Section Break", "insert_after": "workflow_state"},
            {"fieldname": "floating_date", "label": "Floating Date", "fieldtype": "Date", "insert_after": "sb_dates"},
            {"fieldname": "site_visit_date", "label": "Site Visit Date", "fieldtype": "Datetime", "insert_after": "floating_date"},
            {"fieldname": "clarification_deadline", "label": "Clarification Deadline", "fieldtype": "Datetime", "insert_after": "site_visit_date"},
            {"fieldname": "opening_date", "label": "Bid Opening Date", "fieldtype": "Datetime", "insert_after": "deadline"},

            # Financials Section (CPO & Fees)
            {"fieldname": "sb_financials", "label": "Financial Requirements", "fieldtype": "Section Break", "insert_after": "opening_date"},
            {"fieldname": "bid_bond_req", "label": "Bid Bond Required?", "fieldtype": "Check", "insert_after": "sb_financials"},
            {"fieldname": "cpo_amount", "label": "Required CPO Amount", "fieldtype": "Currency", "depends_on": "eval:doc.bid_bond_req==1", "insert_after": "bid_bond_req"},
            {"fieldname": "document_fee", "label": "Document Fee Cost", "fieldtype": "Currency", "insert_after": "cpo_amount"},

            # BOQ & Costing Section
            {"fieldname": "sb_boq", "label": "BOQ & Costing", "fieldtype": "Section Break", "insert_after": "document_fee"},
            {"fieldname": "boq_items", "label": "BOQ Items", "fieldtype": "Table", "options": "Tender BOQ Item", "insert_after": "sb_boq"},
            {"fieldname": "total_cost", "label": "Total Estimated Cost", "fieldtype": "Currency", "read_only": 1, "insert_after": "boq_items"},
            {"fieldname": "total_bid_value", "label": "Total Bid Value", "fieldtype": "Currency", "read_only": 1, "insert_after": "total_cost"},
            
            # Project Link
            {"fieldname": "project_link", "label": "Linked ERPNext Project", "fieldtype": "Link", "options": "Project", "read_only": 1, "insert_after": "workflow_state"}
        ]
    }
    
    create_custom_fields(fields_to_add)
    print("✔ Updated Tender Doctype with SOW Fields")

    # ==============================================================================
    # 4. CLIENT SCRIPT: BOQ CALCULATIONS (Cost + Margin = Price)
    # ==============================================================================
    script_name = "Tender BOQ Logic"
    if frappe.db.exists("Client Script", script_name):
        frappe.delete_doc("Client Script", script_name)

    js_code = """
frappe.ui.form.on('Tender BOQ Item', {
    cost_rate: function(frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },
    margin_percent: function(frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },
    qty: function(frm, cdt, cdn) { calculate_row(frm, cdt, cdn); }
});

function calculate_row(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    // Bid Rate = Cost + (Cost * Margin / 100)
    row.bid_rate = row.cost_rate * (1 + (row.margin_percent / 100));
    row.amount = row.bid_rate * row.qty;
    frm.refresh_field('boq_items');
    calculate_totals(frm);
}

function calculate_totals(frm) {
    let total_cost = 0;
    let total_bid = 0;
    frm.doc.boq_items.forEach(i => {
        total_cost += (i.cost_rate * i.qty);
        total_bid += i.amount;
    });
    frm.set_value('total_cost', total_cost);
    frm.set_value('total_bid_value', total_bid);
}
    """
    
    frappe.get_doc({
        "doctype": "Client Script",
        "dt": "Tender Opportunity",
        "name": script_name,
        "script": js_code,
        "enabled": 1,
        "view": "Form"
    }).insert(ignore_permissions=True)
    print("✔ Installed BOQ Calculation Script")

    # ==============================================================================
    # 5. ALIGN NOTIFICATIONS (CPO Alerts)
    # ==============================================================================
    # Alert 5 Days before CPO Expiry
    if not frappe.db.exists("Notification", "CPO Expiry Alert"):
        doc = frappe.get_doc({
            "doctype": "Notification",
            "name": "CPO Expiry Alert",
            "subject": "⚠️ Action Required: CPO Expiring in 5 Days",
            "document_type": "Bid Security",
            "event": "Days Before",
            "days_in_advance": 5,
            "date_changed": "expiry_date",
            "channel": "System Notification",
            "recipients": [{"receiver_by_role": "Accounts Manager"}],
            "message": """The Bid Bond (CPO) for {{ doc.tender }} is expiring on {{ doc.expiry_date }}. Please contact the client or extend the guarantee."""
        })
        doc.insert(ignore_permissions=True)
        print("✔ Created Notification: CPO Expiry Alert")

    frappe.db.commit()
    print("--- ✅ SOW IMPLEMENTATION COMPLETE ---")

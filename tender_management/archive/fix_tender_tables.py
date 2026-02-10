import frappe

def run():
    print("--- 🛠️ FIXING CHILD TABLES (BOQ, DECISION, COMPETITORS) ---")

    # ==============================================================================
    # 1. CREATE/UPDATE "TENDER BOQ ITEM" (The Missing Piece)
    # ==============================================================================
    if not frappe.db.exists("DocType", "Tender BOQ Item"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Tender BOQ Item",
            "module": "Tender Management",
            "istable": 1,
            "editable_grid": 1,
            "fields": [
                {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "in_list_view": 1},
                {"label": "Description", "fieldname": "description", "fieldtype": "Small Text", "reqd": 1, "in_list_view": 1},
                {"label": "UOM", "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "in_list_view": 1, "columns": 2},
                {"label": "Quantity", "fieldname": "qty", "fieldtype": "Float", "reqd": 1, "in_list_view": 1, "columns": 2},
                {"label": "Rate", "fieldname": "rate", "fieldtype": "Currency", "in_list_view": 1, "columns": 2},
                {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "read_only": 1, "in_list_view": 1, "columns": 2}
            ]
        })
        doc.insert(ignore_permissions=True)
        print("✔ Created Child Table: Tender BOQ Item")
    else:
        print("✔ 'Tender BOQ Item' already exists.")

    # ==============================================================================
    # 2. UPDATE PARENT DOCTYPE TO USE CORRECT TABLES
    # ==============================================================================
    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    updated = False
    for f in doc.fields:
        # Fix Decision Matrix
        if f.fieldname == "decision_matrix":
            if f.options != "Bid Decision Factor":
                f.options = "Bid Decision Factor"
                updated = True
                print("   > Fixed Link: Decision Matrix -> Bid Decision Factor")
        
        # Fix Competitors
        if f.fieldname == "competitors":
            if f.options != "Tender Competitor":
                f.options = "Tender Competitor"
                updated = True
                print("   > Fixed Link: Competitors -> Tender Competitor")
        
        # Fix BOQ Items
        if f.fieldname == "items":
            if f.options != "Tender BOQ Item":
                f.options = "Tender BOQ Item"
                updated = True
                print("   > Fixed Link: Items -> Tender BOQ Item")

    if updated:
        doc.save(ignore_permissions=True)
        print("✔ Parent DocType Updated with Correct Links")
    else:
        print("✔ Parent Links were already correct.")

    frappe.db.commit()
    print("--- ✅ TABLES REPAIRED ---")

if __name__ == "__main__":
    run()

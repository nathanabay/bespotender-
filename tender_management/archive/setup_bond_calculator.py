import frappe

def run():
    print("--- 📅 CONFIGURING BOND VALIDITY CALCULATOR ---")

    dt = "Tender Opportunity"
    doc = frappe.get_doc("DocType", dt)
    
    # 1. ADD 'BOND VALIDITY (DAYS)' FIELD
    # We create a new Int field for the input
    new_field = frappe.new_doc("DocField")
    new_field.fieldname = "bond_validity_days"
    new_field.label = "Bond Validity (Days)"
    new_field.fieldtype = "Int"
    new_field.description = "e.g., 90, 120. Used to calculate expiry."
    new_field.insert_after = "bond_amount" # Place right after amount
    
    # 2. UPDATE 'BOND EXPIRY' TO READ-ONLY
    # It will now be a calculated result, not manual input
    expiry_field = next((f for f in doc.fields if f.fieldname == "bond_expiry"), None)
    
    final_fields = []
    inserted = False
    
    for f in doc.fields:
        final_fields.append(f)
        
        # Inject new field
        if f.fieldname == "bond_amount" and not inserted:
            # Check for duplicates
            if not any(x.fieldname == "bond_validity_days" for x in doc.fields):
                final_fields.append(new_field)
                print("   + Added 'Bond Validity (Days)' field")
            inserted = True
            
        # Lock Expiry Date
        if f.fieldname == "bond_expiry":
            f.read_only = 1
            f.description = "Calculated automatically from Validity Days"
            print("   + Locked 'Bond Expiry' field (System Calculated)")

    doc.fields = final_fields
    doc.save(ignore_permissions=True)
    print("✔ Schema Updated")

    # 3. CREATE CLIENT SCRIPT FOR CALCULATION
    # This runs instantly in the browser
    script_name = "Tender Bond Calculator"
    if frappe.db.exists("Client Script", script_name):
        frappe.delete_doc("Client Script", script_name)

    js_code = """
frappe.ui.form.on('Tender Opportunity', {
    // Trigger on Days change
    bond_validity_days: function(frm) {
        frm.trigger('calculate_expiry');
    },

    // Trigger on Submission Date change (anchor date)
    submission_deadline: function(frm) {
        frm.trigger('calculate_expiry');
    },

    calculate_expiry: function(frm) {
        if (frm.doc.bond_validity_days > 0) {
            // Anchor date: Submission Deadline or Today
            let start_date = frm.doc.submission_deadline || frappe.datetime.now_date();
            
            // Calculate: Start + Days
            let expiry = frappe.datetime.add_days(start_date, frm.doc.bond_validity_days);
            
            frm.set_value('bond_expiry', expiry);
            frappe.show_alert(`Bond expires on: ${expiry} (${frm.doc.bond_validity_days} days)`);
        }
    }
});
    """

    frappe.get_doc({
        "doctype": "Client Script",
        "dt": "Tender Opportunity",
        "name": script_name,
        "script": js_code,
        "enabled": 1,
        "view": "Form"
    }).insert(ignore_permissions=True)

    print("✔ Calculation Logic Installed")
    print("--- ✅ BOND CALCULATOR READY ---")

if __name__ == "__main__":
    run()

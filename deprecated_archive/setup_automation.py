import frappe

def run():
    print("--- 🤖 INSTALLING AUTO-APPROVAL LOGIC ---")

    # 1. CLEANUP OLD SCRIPTS
    script_name = "Tender Auto-Status"
    if frappe.db.exists("Client Script", script_name):
        frappe.delete_doc("Client Script", script_name)

    # 2. DEFINE THE JAVASCRIPT LOGIC
    js_code = """
frappe.ui.form.on('Tender Opportunity', {
    // Trigger when Engineering Decision changes
    eng_approval: function(frm) {
        frm.trigger('update_status');
    },
    // Trigger when Finance Decision changes
    fin_approval: function(frm) {
        frm.trigger('update_status');
    },
    
    // The Logic Engine
    update_status: function(frm) {
        let eng = frm.doc.eng_approval;
        let fin = frm.doc.fin_approval;

        if (eng == 'Approved' && fin == 'Approved') {
            // Success Case
            frm.set_value('workflow_state', 'Approved to Bid');
            frappe.show_alert({message: '🚀 Ready for Bidding!', indicator: 'green'});
        } 
        else if (eng == 'Rejected' || fin == 'Rejected') {
            // Failure Case
            frm.set_value('workflow_state', 'Lost');
            frappe.show_alert({message: '⛔ Marked as No-Go (Lost)', indicator: 'red'});
        }
        else {
            // Still Pending
            frm.set_value('workflow_state', 'Under Evaluation');
        }
    }
});
"""

    # 3. INSERT THE SCRIPT
    doc = frappe.get_doc({
        "doctype": "Client Script",
        "dt": "Tender Opportunity",
        "name": script_name,
        "view": "Form",
        "enabled": 1,
        "script": js_code
    })
    doc.insert(ignore_permissions=True)
    
    frappe.db.commit()
    print("--- ✅ AUTOMATION INSTALLED ---")

if __name__ == "__main__":
    run()

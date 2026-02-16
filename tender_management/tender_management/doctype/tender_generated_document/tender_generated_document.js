frappe.ui.form.on('Tender Generated Document', {
    // refresh: function(frm) {

    // }
    print_pdf: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.file) {
            window.open(row.file, '_blank');
        } else {
            frappe.msgprint(__('No PDF file found for this document.'));
        }
    }
});

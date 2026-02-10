frappe.ui.form.on("Tender Opportunity", {
    refresh: function (frm) {
        apply_wf_logic(frm);
    },

    workflow_state: function (frm) {
        apply_wf_logic(frm);
    },

    sector: function (frm) {
        if (frm.doc.sector == 'Construction') {
            frm.set_value('naming_series', 'T-CON-.YYYY.-.####');
        } else if (frm.doc.sector == 'Electro-Mechanical') {
            frm.set_value('naming_series', 'T-ELEC-.YYYY.-.####');
        } else if (frm.doc.sector == 'Maintenance') {
            frm.set_value('naming_series', 'T-WAT-.YYYY.-.####');
        } else if (frm.doc.sector == 'Water Works') {
            frm.set_value('naming_series', 'T-WAT-.YYYY.-.####');
        } else {
            frm.set_value('naming_series', 'T-CON-.YYYY.-.####'); // Default
        }
    }
});

function apply_wf_logic(frm) {
    let state = frm.doc.workflow_state;

    // 1. TAB & SECTION VISIBILITY (Unfolding the form)
    // tab_opportunity is always visible

    // Hide specialized tabs by default
    frm.set_df_property('tab_decision', 'hidden', 1);
    frm.set_df_property('tab_procurement', 'hidden', 1);
    frm.set_df_property('tab_proposal', 'hidden', 1);
    frm.set_df_property('tab_analysis', 'hidden', 1);

    if (state !== "Draft") {
        frm.set_df_property('tab_decision', 'hidden', 0);
    }

    if (state === "Approved to Bid" || state === "Tender Purchased" || state === "Bid Bond Issued" || state === "Technical Preparation" || state === "Financial Preparation" || state === "Ready for Submission" || state === "Submitted" || state === "Won" || state === "Lost") {
        frm.set_df_property('tab_procurement', 'hidden', 0);
    }

    if (state === "Bid Bond Issued" || state === "Technical Preparation" || state === "Financial Preparation" || state === "Ready for Submission" || state === "Submitted" || state === "Won" || state === "Lost") {
        frm.set_df_property('tab_proposal', 'hidden', 0);
    }

    if (state === "Submitted" || state === "Won" || state === "Lost") {
        frm.set_df_property('tab_analysis', 'hidden', 0);
    }

    // Secondary Section visibility within tabs
    frm.set_df_property('sec_security', 'hidden', (state === "Approved to Bid")); // Hide bond section until purchased

    // 2. MANDATORY FIELDS (Conditional Enforcement)
    frm.set_df_property('purchase_date', 'reqd', (state === "Tender Purchased"));
    frm.set_df_property('purchase_receipt_no', 'reqd', (state === "Tender Purchased"));

    frm.set_df_property('bond_type', 'reqd', (state === "Bid Bond Issued"));
    frm.set_df_property('bond_number', 'reqd', (state === "Bid Bond Issued"));
    frm.set_df_property('bank_name', 'reqd', (state === "Bid Bond Issued"));

    frm.set_df_property('technical_proposal', 'reqd', (state === "Ready for Submission"));
    frm.set_df_property('financial_proposal_doc', 'reqd', (state === "Ready for Submission"));

    // 3. HEADLINE ALERTS (User Guidance)
    if (state === "Draft") {
        frm.dashboard.set_headline_alert(__("Step 1: Fill in basic details and Submit for Review."), "blue");
    } else if (state === "Pending Review") {
        frm.dashboard.set_headline_alert(__("Step 2: Waiting for Manager Review."), "orange");
    } else if (state === "Approved to Bid") {
        frm.dashboard.set_headline_alert(__("Step 3: Tender Approved. Please purchase the document and enter receipt info."), "green");
    } else if (state === "Tender Purchased") {
        frm.dashboard.set_headline_alert(__("Step 4: Document Purchased. Please issue the Bid Bond (CPO) to proceed."), "green");
    } else if (state === "Bid Bond Issued") {
        frm.dashboard.set_headline_alert(__("Step 5: Bond Active. Start Technical Preparation."), "green");
    } else if (state === "Technical Preparation") {
        frm.dashboard.set_headline_alert(__("Step 6: Technical Stage. Progress to Financial Preparation when ready."), "blue");
    } else if (state === "Ready for Submission") {
        frm.dashboard.set_headline_alert(__("Step 7: All documents ready. Please submit the bid to the client."), "blue");
    } else if (state === "Submitted") {
        frm.dashboard.set_headline_alert(__("Step 8: Bid Submitted. Awaiting Award/Tender result."), "orange");
    }
}

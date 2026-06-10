// Copyright (c) 2026, bespo and contributors
// For license information, please see license.txt

frappe.ui.form.on('Scraped Tender', {
	refresh: function(frm) {
		// Scraper Launch Button
		frm.add_custom_button(__('Scrape Tenders'), function() {
			frappe.call({
				method: "tender_management.utils.scraper_utils.run_scraper_job",
				callback: function(r) {
					if (r.message && r.message.status === "success") {
						frappe.show_alert({
							message: __('Scraping job enqueued successfully'),
							indicator: 'green'
						});
					}
				}
			});
		}, __("Actions"));

		// Stop Scraper Button
		frm.add_custom_button(__('Stop Scraping'), function() {
			frappe.confirm(__('Are you sure you want to stop all active scraping processes?'), function() {
				frappe.call({
					method: "tender_management.utils.scraper_utils.stop_scraper_job",
					callback: function(r) {
						if (r.message && r.message.status === "success") {
							frappe.show_alert({
								message: __('Scraping stopped successfully'),
								indicator: 'green'
							});
						} else {
							frappe.msgprint({
								title: __('Error'),
								indicator: 'red',
								message: r.message ? r.message.message : __('Unknown error occurred')
							});
						}
					}
				});
			});
		}, __("Actions"));

		// Create Tender Opportunity Button
		frm.add_custom_button(__('Create Tender Opportunity'), function() {
			// Helper to extract numbers from strings like "200 ETB"
			const extract_number = (str) => {
				if (!str) return 0;
				let num = String(str).replace(/[^0-9.]/g, '');
				return num ? parseFloat(num) : 0;
			};

			const create_opportunity = () => {
				let raw_title = frm.doc.tender_title || frm.doc.title || "";
				let combined_description = `<b>AI Summary:</b><br>${frm.doc.ai_summary || "N/A"}<br><br><b>Original Description:</b><br>${frm.doc.description || "N/A"}`;
				
				frappe.new_doc('Tender Opportunity', {
					title: raw_title.substring(0, 140),
					publication_date: frm.doc.posted_date ? String(frm.doc.posted_date).split(' ')[0] : null,
					submission_deadline: frm.doc.closing_date,
					tender_link: frm.doc.source_url,
					url: frm.doc.source_url,
					document_price: extract_number(frm.doc.bid_document_price),
					bond_amount: extract_number(frm.doc.bid_bond),
					full_tender_document: frm.doc.documents,
					solution_overview: combined_description
				});
			};
			
			// Change status to Processed when creating an opportunity
			if (frm.doc.status !== "Processed") {
				frm.set_value("status", "Processed");
				frm.save().then(() => {
					create_opportunity();
				});
			} else {
				create_opportunity();
			}

		}).addClass('btn-primary');
	}
});

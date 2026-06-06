// Copyright (c) 2026, bespo and contributors
// For license information, please see license.txt

frappe.ui.form.on('Scraped Tender', {
	refresh: function(frm) {
		frm.add_custom_button(__('Scrape Tenders'), function() {
			frappe.call({
				method: "tender_management.utils.run_scraper.run_scraper_job",
				callback: function(r) {
					if (r.message && r.message.status === "success") {
						frappe.msgprint(__('Scraping job has been enqueued. It will take a few minutes to finish.'));
					}
				}
			});
		}, __("Actions"));
	}
});

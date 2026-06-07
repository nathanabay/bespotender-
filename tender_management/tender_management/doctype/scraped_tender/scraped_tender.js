// Copyright (c) 2026, bespo and contributors
// For license information, please see license.txt

frappe.ui.form.on('Scraped Tender', {
	refresh: function(frm) {
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
	}
});

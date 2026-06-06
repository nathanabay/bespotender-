frappe.listview_settings['Scraped Tender'] = {
	refresh: function(listview) {
		// Add as a prominent button in the header
		listview.page.add_inner_button(__('Scrape Tenders'), function() {
			frappe.call({
				method: "tender_management.utils.run_scraper.run_scraper_job",
				callback: function(r) {
					if (r.message && r.message.status === "success") {
						frappe.msgprint(__('Scraping job has been enqueued. It will take a few minutes to finish.'));
					}
				}
			});
		});

		// Also keep it in the menu just in case
		listview.add_menu_item(__('Scrape Tenders'), function() {
			frappe.call({
				method: "tender_management.utils.run_scraper.run_scraper_job",
				callback: function(r) {
					if (r.message && r.message.status === "success") {
						frappe.msgprint(__('Scraping job has been enqueued.'));
					}
				}
			});
		});
	}
};

// Copyright (c) 2026, bespo and contributors
// For license information, please see license.txt

frappe.listview_settings['Scraped Tender'] = {
	refresh: function(listview) {
		console.log("Scraped Tender list view loaded");
		// Add as a prominent button in the header
		listview.page.add_inner_button(__('Scrape Tenders'), function() {
			frappe.confirm(__('This will start a background job to scrape up to 80 pages of tenders. Proceed?'), function() {
				frappe.call({
					method: "tender_management.utils.scraper_utils.run_scraper_job",
					callback: function(r) {
						if (r.message && r.message.status === "success") {
							frappe.show_alert({
								message: __('Scraping job enqueued successfully'),
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
		});
	},
	get_indicator: function(doc) {
		if (doc.status === "New") {
			return [__("New"), "blue", "status,=,New"];
		} else if (doc.status === "Processed") {
			return [__("Processed"), "green", "status,=,Processed"];
		} else if (doc.status === "Error") {
			return [__("Error"), "red", "status,=,Error"];
		}
	},
	format_render: function(data) {
		// Custom rendering for the list items to mimic 2merkato look
		// This can be used for more advanced UI if needed
	}
};

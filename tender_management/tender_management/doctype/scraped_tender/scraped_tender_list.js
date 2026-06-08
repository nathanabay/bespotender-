// Copyright (c) 2026, bespo and contributors
// For license information, please see license.txt

frappe.listview_settings['Scraped Tender'] = {
	onload: function(listview) {
		// Inject custom CSS to wrap ALL text including ID
		const style = `
			/* Increase row height and allow wrapping for all columns */
			.frappe-list .list-row {
				height: auto !important;
				min-height: 100px !important;
				padding-top: 15px !important;
				padding-bottom: 15px !important;
				align-items: center !important;
			}
			
			/* Force all text in the list to wrap - including IDs and spans */
			.frappe-list .list-row .level-item, 
			.frappe-list .list-row .list-column,
			.frappe-list .list-row .list-subject,
			.frappe-list .list-row .list-id,
			.frappe-list .list-row div,
			.frappe-list .list-row span,
			.frappe-list .list-row a {
				white-space: normal !important;
				word-break: break-all !important;
				line-height: 1.5 !important;
				display: inline-block !important;
			}

			/* Specific targeting for the ID/Name column */
			.frappe-list .list-row .list-column.list-subject,
			.frappe-list .list-row .level-item.ellipsis {
				max-width: none !important;
				overflow: visible !important;
				text-overflow: clip !important;
			}

			/* Style the subject (Tender Title) */
			.frappe-list .list-row .list-subject {
				font-weight: 600 !important;
				font-size: 14px !important;
				color: #111827 !important;
				min-width: 300px !important;
			}

			/* Ensure specific columns have enough breathing room */
			.frappe-list .list-row .list-column {
				padding-right: 15px !important;
			}
		`;
		$('<style>').text(style).appendTo('head');
	},
	refresh: function(listview) {
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

		// Add a Stop button
		listview.page.add_inner_button(__('Stop Scraping'), function() {
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
		}).css({ 'color': '#ff4d4f' });
	},
	get_indicator: function(doc) {
		if (doc.status === "New") {
			return [__("New"), "blue", "status,=,New"];
		} else if (doc.status === "Processed") {
			return [__("Processed"), "green", "status,=,Processed"];
		} else if (doc.status === "Error") {
			return [__("Error"), "red", "status,=,Error"];
		}
	}
};

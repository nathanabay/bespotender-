// Copyright (c) 2026, bespo and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tender Scraper Settings', {
	refresh: function(frm) {
		// Sync Categories from 2merkato website
		frm.add_custom_button(__('Sync Categories from 2merkato'), function() {
			frappe.show_alert({
				message: __('Starting category sync...'),
				indicator: 'blue'
			});
			frappe.call({
				method: "tender_management.utils.scraper_utils.sync_categories",
				callback: function(r) {
					if (r.message && r.message.status === "success") {
						let msg = r.message.new_count > 0 
							? __('{0} new categories added. Total: {1}', [r.message.new_count, r.message.total_count])
							: __('All {0} categories are already up to date.', [r.message.total_count]);
							
						frappe.msgprint({
							title: __('Category Sync'),
							indicator: 'green',
							message: msg
						});
					}
				}
			});
		}, __("Actions"));

		// Add All available categories to the filter table
		frm.add_custom_button(__('Add All Categories to Table'), function() {
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Merkato Category",
					fields: ["name"],
					limit_page_length: 500,
					order_by: "category_name asc"
				},
				callback: function(r) {
					if (r.message) {
						// Clear existing
						frm.clear_table("categories");
						
						// Add all
						r.message.forEach(cat => {
							let row = frm.add_child("categories");
							row.category_name = cat.name;
						});
						
						frm.refresh_field("categories");
						frappe.show_alert({
							message: __('Added {0} categories to the table.', [r.message.length]),
							indicator: 'green'
						});
					}
				}
			});
		}, __("Actions"));
	}
});

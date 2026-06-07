// Copyright (c) 2026, bespo and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tender Scraper Settings', {
	refresh: function(frm) {
		// Helper function to add all categories to the table
		const add_all_to_table = () => {
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
						frm.clear_table("categories");
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
		};

		// 1. Primary Button: Sync and Fill Table
		frm.add_custom_button(__('Sync & Fill Category Table'), function() {
			frappe.show_alert({
				message: __('Syncing categories from 2merkato...'),
				indicator: 'blue'
			});
			frappe.call({
				method: "tender_management.utils.scraper_utils.sync_categories",
				callback: function(r) {
					if (r.message && r.message.status === "success") {
						let msg = r.message.new_count > 0 
							? `Added ${r.message.new_count} new categories. Total: ${r.message.total_count}`
							: `All ${r.message.total_count} categories are already up to date.`;
						
						frappe.confirm(`${msg}<br><br><b>Would you like to fill your "Categories to Scrape" table with all ${r.message.total_count} categories?</b>`, () => {
							add_all_to_table();
						});
					}
				}
			});
		}).addClass('btn-primary');

		// 2. Secondary Button: Just fill table from existing master list
		frm.add_custom_button(__('Just Fill Table (No Sync)'), function() {
			add_all_to_table();
		}, __("Actions"));

		// 3. Secondary Button: Just sync master list (no fill)
		frm.add_custom_button(__('Just Sync List (No Fill)'), function() {
			frappe.call({
				method: "tender_management.utils.scraper_utils.sync_categories",
				callback: function(r) {
					if (r.message && r.message.status === "success") {
						frappe.msgprint(`Sync complete. Total categories: ${r.message.total_count}`);
					}
				}
			});
		}, __("Actions"));
	}
});

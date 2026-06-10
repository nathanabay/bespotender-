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
							row.enabled = 1; // Explicitly enable by default when adding all
						});
						frm.refresh_field("categories");
						frappe.show_alert({
							message: __('Added {0} categories to the table and enabled them.', [r.message.length]),
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

		// 2. Just fill table from existing master list
		frm.add_custom_button(__('Just Fill Table (No Sync)'), function() {
			add_all_to_table();
		}, __("Actions"));

		// 3. Just sync master list (no fill)
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

		// 4. Select All in Table (Directly on form)
		frm.add_custom_button(__('Select All (Check All)'), function() {
			if (!frm.doc.categories || frm.doc.categories.length === 0) {
				frappe.msgprint(__('The categories table is empty.'));
				return;
			}
			frm.doc.categories.forEach(row => {
				frappe.model.set_value(row.doctype, row.name, 'enabled', 1);
			});
			frappe.show_alert({ message: __('Checked all rows. Please click Save.'), indicator: 'green' });
		});

		// 5. Deselect All in Table (Directly on form)
		frm.add_custom_button(__('Deselect All (Uncheck All)'), function() {
			if (!frm.doc.categories || frm.doc.categories.length === 0) {
				frappe.msgprint(__('The categories table is empty.'));
				return;
			}
			frm.doc.categories.forEach(row => {
				frappe.model.set_value(row.doctype, row.name, 'enabled', 0);
			});
			frappe.show_alert({ message: __('Unchecked all rows. Please click Save.'), indicator: 'orange' });
		});
		// 6. Check Scraper Status
		frm.add_custom_button(__('Check Scraper Status'), function() {
			frappe.call({
				method: "tender_management.utils.scraper_utils.check_scraper_status",
				callback: function(r) {
					if (r.message && r.message.status === "success") {
						frappe.msgprint({
							title: __('Scraper Status'),
							indicator: r.message.is_running ? 'green' : 'orange',
							message: `<b>${r.message.message}</b>`
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
	}
});

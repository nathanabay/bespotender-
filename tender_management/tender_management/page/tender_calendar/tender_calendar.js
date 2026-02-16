frappe.pages['tender-calendar'].on_page_load = function (wrapper) {
	console.log("📅 Tender Calendar (v6): Page Load Triggered");
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Tender Calendar',
		single_column: true
	});

	// Add filters to the sidebar/header
	page.add_field({
		label: 'Sector',
		fieldname: 'sector_filter',
		fieldtype: 'Select',
		options: ["", "Construction", "Electro-Mechanical", "Maintenance", "Water Works", "General Supply"],
		change: function () {
			page.calendar.refetchEvents();
		}
	});

	page.add_field({
		label: 'Status',
		fieldname: 'status_filter',
		fieldtype: 'Select',
		options: ["", "Open", "Closed"],
		change: function () {
			page.calendar.refetchEvents();
		}
	});

	// Create calendar container
	let calendar_wrapper = $('<div id="tender-calendar-view" style="padding: 20px; min-height: 600px;"></div>').appendTo(page.main);

	// Load FullCalendar assets from CDN since local bundle is missing
	frappe.require([
		"https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js",
		"https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css"
	], function () {
		console.log("📅 Tender Calendar: FullCalendar Assets Loaded from CDN");
		initialize_calendar(calendar_wrapper, page);
	});
}

function initialize_calendar(wrapper, page) {
	let calendarEl = wrapper[0];
	if (!calendarEl) {
		console.error("📅 Tender Calendar: Wrapper element not found!");
		return;
	}

	if (typeof FullCalendar === 'undefined') {
		console.error("📅 Tender Calendar: FullCalendar library not loaded!");
		frappe.msgprint("Error: Calendar library could not be loaded.");
		return;
	}

	console.log("📅 Tender Calendar: Initializing FullCalendar...");

	let calendar = new FullCalendar.Calendar(calendarEl, {
		initialView: 'dayGridMonth',
		headerToolbar: {
			left: 'prev,next today',
			center: 'title',
			right: 'dayGridMonth,timeGridWeek,listWeek'
		},
		events: function (info, successCallback, failureCallback) {
			// Get current filter values
			let sector = page.get_form_values().sector_filter;
			let status = page.get_form_values().status_filter;

			console.log("📅 Tender Calendar: Fetching events", { start: info.startStr, end: info.endStr, sector, status });

			frappe.call({
				method: 'tender_management.tender_management.page.tender_calendar.tender_calendar.get_calendar_events',
				args: {
					start: info.startStr,
					end: info.endStr,
					filters: {
						sector: sector,
						status: status
					}
				},
				callback: function (r) {
					if (r.message) {
						console.log("📅 Tender Calendar: Events fetched successfully", r.message.length);
						successCallback(r.message);
					} else {
						console.warn("📅 Tender Calendar: No events returned");
						successCallback([]);
					}
				},
				error: function (err) {
					console.error("📅 Tender Calendar: API Error", err);
					failureCallback();
				}
			});
		},
		eventClick: function (info) {
			console.log("📅 Tender Calendar: Event clicked", info.event);
			frappe.set_route('Form', 'Tender Opportunity', info.event.extendedProps.tender);
		},
		eventClassNames: function (arg) {
			return arg.event.extendedProps.className || [];
		}
	});

	calendar.render();
	page.calendar = calendar; // Store calendar in page object for accessibility
	console.log("📅 Tender Calendar: Render called");

	page.clear_inner_toolbar();
	page.add_inner_button(__('This Month'), function () {
		calendar.gotoDate(new Date());
	});

	page.add_inner_button(__('Refresh'), function () {
		calendar.refetchEvents();
	});
}

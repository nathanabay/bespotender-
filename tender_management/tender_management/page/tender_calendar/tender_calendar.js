frappe.pages['tender-calendar'].on_page_load = function (wrapper) {
	console.log("📅 Tender Calendar: Page Load Triggered");
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Tender Calendar',
		single_column: true
	});

	// Create calendar container
	let calendar_wrapper = $('<div id="tender-calendar-view" style="padding: 20px; min-height: 600px;"></div>').appendTo(page.main);

	// Load FullCalendar assets
	// Frappe typically stores libs in frappe/public/js/lib...
	// We'll try to load the bundle if available, or individual files.
	// For v13/v14/v15, 'fullcalendar.bundle.js' is often standard.
	frappe.require([
		"assets/frappe/js/lib/fullcalendar/main.min.js",
		"assets/frappe/js/lib/fullcalendar/main.min.css"
	], function () {
		console.log("📅 Tender Calendar: FullCalendar Assets Loaded");
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
			console.log("📅 Tender Calendar: Fetching events for range", info.startStr, "to", info.endStr);
			frappe.call({
				method: 'tender_management.page.tender_calendar.tender_calendar.get_calendar_events',
				args: {
					start: info.startStr,
					end: info.endStr
				},
				callback: function (r) {
					if (r.message) {
						console.log("📅 Tender Calendar: Events fetched successfully", r.message.length);
						successCallback(r.message);
					} else {
						console.warn("📅 Tender Calendar: No events returned");
						successCallback([]); // Return empty array to avoid error
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
			// Open the tender opportunity when clicked
			frappe.set_route('Form', 'Tender Opportunity', info.event.extendedProps.tender);
		},
		eventClassNames: function (arg) {
			return arg.event.extendedProps.className || [];
		}
	});

	calendar.render();
	console.log("📅 Tender Calendar: Render called");

	// Add filter buttons after calendar is initialized
	page.clear_inner_toolbar();
	page.add_inner_button(__('This Month'), function () {
		calendar.gotoDate(new Date());
	});

	page.add_inner_button(__('Refresh'), function () {
		calendar.refetchEvents();
	});
}

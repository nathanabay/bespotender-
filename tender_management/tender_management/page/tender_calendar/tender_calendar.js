frappe.pages['tender-calendar'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Tender Calendar',
		single_column: true
	});

	// Create calendar container
	let calendar_wrapper = $('<div id="tender-calendar-view" style="padding: 20px;"></div>').appendTo(page.main);

	// Initialize FullCalendar
	let calendarEl = calendar_wrapper[0];
	let calendar = new FullCalendar.Calendar(calendarEl, {
		initialView: 'dayGridMonth',
		headerToolbar: {
			left: 'prev,next today',
			center: 'title',
			right: 'dayGridMonth,timeGridWeek,listWeek'
		},
		events: function (info, successCallback, failureCallback) {
			frappe.call({
				method: 'tender_management.page.tender_calendar.tender_calendar.get_calendar_events',
				args: {
					start: info.startStr,
					end: info.endStr
				},
				callback: function (r) {
					if (r.message) {
						successCallback(r.message);
					} else {
						failureCallback();
					}
				},
				error: function () {
					failureCallback();
				}
			});
		},
		eventClick: function (info) {
			// Open the tender opportunity when clicked
			frappe.set_route('Form', 'Tender Opportunity', info.event.extendedProps.tender);
		},
		eventClassNames: function (arg) {
			return arg.event.extendedProps.className || [];
		}
	});

	calendar.render();

	// Add filter buttons after calendar is initialized
	page.add_inner_button(__('This Month'), function () {
		calendar.gotoDate(new Date());
	});

	page.add_inner_button(__('Refresh'), function () {
		calendar.refetchEvents();
	});
}

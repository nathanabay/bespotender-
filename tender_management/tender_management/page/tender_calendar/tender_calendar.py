# Copyright (c) 2026, BES and contributors
# For license information, please see license.txt

import frappe

@frappe.whitelist()
def get_calendar_events(start, end, filters=None):
	"""
	Get all tender opportunities for the calendar view
	Args:
		start: Start date
		end: End date
		filters: Optional JSON string of filters
	Returns:
		list: Calendar events
	"""
	if not frappe.has_permission("Tender Opportunity", "read"):
		frappe.throw(frappe._("You do not have permission to view Tender Opportunities"), frappe.PermissionError)

	events = []
	
	# Parse filters if provided
	query_filters = [
		["submission_deadline", ">=", start],
		["submission_deadline", "<=", end],
	]
	
	if filters:
		additional_filters = frappe.parse_json(filters)
		for key, value in additional_filters.items():
			if value:
				query_filters.append([key, "=", value])
	
	# Fetch all tender opportunities in the date range
	tenders = frappe.get_all(
		"Tender Opportunity",
		filters=query_filters,
		fields=["name", "title", "client", "submission_deadline", "publication_date", 
		        "site_visit_date", "pre_bid_meeting_date", "workflow_state", "sector"]
	)
	
	for tender in tenders:
		# Add submission deadline event
		if tender.submission_deadline:
			events.append({
				"title": f"[DEADLINE] {tender.title}",
				"start": tender.submission_deadline,
				"end": tender.submission_deadline,
				"allDay": False,
				"tender": tender.name,
				"type": "deadline",
				"className": get_event_class(tender.workflow_state)
			})
		
		# Add publication date event
		if tender.publication_date:
			events.append({
				"title": f"[PUBLISHED] {tender.title}",
				"start": tender.publication_date,
				"end": tender.publication_date,
				"allDay": True,
				"tender": tender.name,
				"type": "publication",
				"className": "event-publication"
			})
		
		# Add site visit event
		if tender.site_visit_date:
			events.append({
				"title": f"[SITE VISIT] {tender.title}",
				"start": tender.site_visit_date,
				"end": tender.site_visit_date,
				"allDay": False,
				"tender": tender.name,
				"type": "site_visit",
				"className": "event-site-visit"
			})
		
		# Add pre-bid meeting event
		if tender.pre_bid_meeting_date:
			events.append({
				"title": f"[PRE-BID] {tender.title}",
				"start": tender.pre_bid_meeting_date,
				"end": tender.pre_bid_meeting_date,
				"allDay": False,
				"tender": tender.name,
				"type": "pre_bid",
				"className": "event-pre-bid"
			})
	
	return events

def get_event_class(workflow_state):
	"""Return CSS class based on workflow state"""
	state_colors = {
		"Draft": "event-draft",
		"Pending Review": "event-review",
		"Approved to Bid": "event-approved",
		"Submitted": "event-submitted",
		"Won": "event-won",
		"Lost": "event-lost"
	}
	return state_colors.get(workflow_state, "event-default")

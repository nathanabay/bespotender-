"""
tender_management/tender_management/setup/charts.py

Dashboard chart and number-card setup extracted from the monolithic setup.py.
"""
import json
import frappe


def setup_dashboard_charts():
	upsert_dashboard_chart("Tender Pipeline Value", {
		"doctype": "Dashboard Chart", "chart_name": "Tender Pipeline Value",
		"chart_type": "Group By", "document_type": "Tender Opportunity",
		"group_by_based_on": "workflow_state",
		"aggregate_function_based_on": "final_bid_price",
		"aggregate_function": "Sum", "type": "Bar",
		"timeseries": 0, "is_public": 1, "filters_json": "[]",
		"module": "Tender Management",
	})
	upsert_dashboard_chart("Win Loss Ratio", {
		"doctype": "Dashboard Chart", "chart_name": "Win Loss Ratio",
		"chart_type": "Group By", "document_type": "Tender Opportunity",
		"group_by_based_on": "workflow_state",
		"aggregate_function": "Count", "based_on": "creation",
		"timeseries": 0,
		"filters_json": json.dumps([["Tender Opportunity", "workflow_state", "in", ["Approved", "Rejected"]]]),
		"type": "Donut", "is_public": 1, "module": "Tender Management",
	})
	upsert_dashboard_chart("Tenders by Sector", {
		"doctype": "Dashboard Chart", "chart_name": "Tenders by Sector",
		"chart_type": "Group By", "document_type": "Tender Opportunity",
		"group_by_based_on": "sector", "aggregate_function": "Count",
		"type": "Donut", "is_public": 1, "filters_json": "[]",
		"module": "Tender Management",
	})
	upsert_dashboard_chart("Monthly Publication Trend", {
		"doctype": "Dashboard Chart", "chart_name": "Monthly Publication Trend",
		"chart_type": "Count", "document_type": "Tender Opportunity",
		"based_on": "publication_date", "timeseries": 1,
		"time_interval": "Monthly", "timespan": "Last Year",
		"type": "Line", "is_public": 1, "filters_json": "[]",
		"module": "Tender Management",
	})
	upsert_dashboard_chart("Bond Type Distribution", {
		"doctype": "Dashboard Chart", "chart_name": "Bond Type Distribution",
		"chart_type": "Group By", "document_type": "Tender Opportunity",
		"group_by_based_on": "bond_type", "aggregate_function": "Count",
		"type": "Pie", "is_public": 1, "filters_json": "[]",
		"module": "Tender Management",
	})
	upsert_dashboard_chart("Tasks by Status", {
		"doctype": "Dashboard Chart", "chart_name": "Tasks by Status",
		"chart_type": "Group By", "document_type": "Tender Task",
		"group_by_based_on": "status", "aggregate_function": "Count",
		"type": "Donut", "is_public": 1, "filters_json": "[]",
		"module": "Tender Management",
	})


def upsert_dashboard_chart(name, doct):
	if not frappe.db.exists("Dashboard Chart", name):
		frappe.get_doc(doct).insert(ignore_permissions=True)
		print(f"  ✔ Created Dashboard Chart: {name}")
		return

	doc = frappe.get_doc("Dashboard Chart", name)
	recreate = (
		(doct.get("chart_type") and doc.chart_type != doct["chart_type"])
		or (doct.get("document_type") and doc.document_type != doct["document_type"])
	)
	if recreate:
		frappe.delete_doc("Dashboard Chart", name, ignore_permissions=True)
		frappe.get_doc(doct).insert(ignore_permissions=True)
		print(f"  ✔ Recreated Dashboard Chart: {name}")
	else:
		doct.pop("chart_type", None)
		doct.pop("document_type", None)
		doc.update(doct)
		doc.save(ignore_permissions=True)
		print(f"  ✔ Updated Dashboard Chart: {name}")


def setup_number_cards():
	_ensure_card("Total Active Tenders", {
		"doctype": "Number Card", "name": "Total Active Tenders",
		"label": "Total Active Tenders", "document_type": "Tender Opportunity",
		"function": "Count", "is_public": 1,
		"show_percentage_stats": 1, "stats_time_interval": "Monthly",
		"filters_json": json.dumps([["Tender Opportunity", "status", "!=", "Completed"]]),
		"module": "Tender Management",
	})
	_ensure_card("Total Won Value", {
		"doctype": "Number Card", "name": "Total Won Value",
		"label": "Total Won Value", "document_type": "Tender Opportunity",
		"function": "Sum", "aggregate_function_based_on": "final_bid_price",
		"is_public": 1, "show_percentage_stats": 1, "stats_time_interval": "Monthly",
	})
	_ensure_card("My Open Tasks", {
		"doctype": "Number Card", "name": "My Open Tasks",
		"label": "My Open Tasks", "document_type": "Tender Task",
		"function": "Count", "is_public": 1,
		"show_percentage_stats": 1, "stats_time_interval": "Monthly",
		"filters_json": json.dumps([
			["Tender Task", "status", "in", ["Open", "In Progress"]],
			["Tender Task", "assigned_to", "=", "frappe.session.user"],
		]),
		"module": "Tender Management",
	})


def _ensure_card(name, doct):
	if not frappe.db.exists("Number Card", name):
		frappe.get_doc(doct).insert(ignore_permissions=True)
		print(f"  ✔ Created Number Card: {name}")
	else:
		print(f"  ✔ Number Card already exists: {name}")

"""
tender_management/tender_management/setup/workspace.py

Creates or updates the 'Tender Management' Frappe Workspace.
"""
import json
import frappe


def setup_workspace():
	workspace_name = "Tender Management"

	ws_content = [
		{"type": "header", "data": {"text": "Key Insights", "level": 2, "col": 12}},
		{"type": "card", "data": {"card_name": "Total Active Tenders", "col": 4}},
		{"type": "card", "data": {"card_name": "Total Won Value", "col": 4}},
		{"type": "header", "data": {"text": "Performance & Pipeline", "level": 2, "col": 12}},
		{"type": "chart", "data": {"chart_name": "Tender Pipeline Value", "col": 8}},
		{"type": "chart", "data": {"chart_name": "Win Loss Ratio", "col": 4}},
		{"type": "header", "data": {"text": "Trends & Analysis", "level": 2, "col": 12}},
		{"type": "chart", "data": {"chart_name": "Monthly Publication Trend", "col": 12}},
		{"type": "chart", "data": {"chart_name": "Tenders by Sector", "col": 6}},
		{"type": "chart", "data": {"chart_name": "Bond Type Distribution", "col": 6}},
		{"type": "header", "data": {"text": "Quick Actions", "level": 3, "col": 12}},
		{"type": "shortcut", "data": {"shortcut_name": "Tenders", "col": 3}},
		{"type": "shortcut", "data": {"shortcut_name": "Tasks", "col": 3}},
		{"type": "shortcut", "data": {"shortcut_name": "Calendar View", "col": 3}},
		{"type": "shortcut", "data": {"shortcut_name": "Bid Decisions", "col": 3}},
		{"type": "shortcut", "data": {"shortcut_name": "Cost Estimations", "col": 3}},
		{"type": "shortcut", "data": {"shortcut_name": "Templates", "col": 3}},
		{"type": "shortcut", "data": {"shortcut_name": "Scraper Settings", "col": 3}},
		{"type": "header", "data": {"text": "Task Overview", "level": 3, "col": 12}},
		{"type": "chart", "data": {"chart_name": "Tasks by Status", "col": 6}},
		{"type": "card", "data": {"card_name": "My Open Tasks", "col": 6}},
		{"type": "header", "data": {"text": "Contract Management", "level": 3, "col": 12}},
		{"type": "shortcut", "data": {"shortcut_name": "Performance Bonds", "col": 3}},
		{"type": "header", "data": {"text": "Intelligence", "level": 3, "col": 12}},
		{"type": "shortcut", "data": {"shortcut_name": "Competitors", "col": 3}},
	]

	charts = [
		{"chart_name": "Tender Pipeline Value", "label": "Tender Pipeline Value"},
		{"chart_name": "Win Loss Ratio", "label": "Win Loss Ratio"},
		{"chart_name": "Monthly Publication Trend", "label": "Monthly Publication Trend"},
		{"chart_name": "Tenders by Sector", "label": "Tenders by Sector"},
		{"chart_name": "Bond Type Distribution", "label": "Bond Type Distribution"},
		{"chart_name": "Tasks by Status", "label": "Tasks by Status"},
	]

	number_cards = [
		{"number_card_name": "Total Active Tenders", "label": "Total Active Tenders"},
		{"number_card_name": "Total Won Value", "label": "Total Won Value"},
		{"number_card_name": "My Open Tasks", "label": "My Open Tasks"},
	]

	shortcuts = [
		{"link_to": "Tender Opportunity", "type": "DocType", "label": "Tenders", "icon": "list", "color": "Grey"},
		{"link_to": "Tender Task", "type": "DocType", "label": "Tasks", "icon": "check", "color": "Blue"},
		{"link_to": "tender-calendar", "type": "Page", "label": "Calendar View", "icon": "calendar", "color": "Orange"},
		{"link_to": "Bid Decision Matrix", "type": "DocType", "label": "Bid Decisions", "icon": "milestone", "color": "Purple"},
		{"link_to": "Cost Estimation", "type": "DocType", "label": "Cost Estimations", "icon": "calculator", "color": "Green"},
		{"link_to": "Document Template", "type": "DocType", "label": "Templates", "icon": "file", "color": "Cyan"},
		{"link_to": "Tender Scraper Settings", "type": "DocType", "label": "Scraper Settings", "icon": "settings", "color": "Grey"},
		{"link_to": "Performance Bond", "type": "DocType", "label": "Performance Bonds", "icon": "shield", "color": "Red"},
		{"link_to": "Competitor", "type": "DocType", "label": "Competitors", "icon": "users", "color": "Yellow"},
	]

	ws_doc = {
		"doctype": "Workspace", "name": workspace_name, "label": workspace_name,
		"title": workspace_name, "category": "Modules", "module": "Tender Management",
		"icon": "folder", "public": 1,
		"charts": charts, "number_cards": number_cards, "shortcuts": shortcuts,
		"content": json.dumps(ws_content), "is_hidden": 0,
	}

	if not frappe.db.exists("Workspace", workspace_name):
		frappe.get_doc(ws_doc).insert(ignore_permissions=True)
		print(f"  ✔ Created Workspace: {workspace_name}")
	else:
		doc = frappe.get_doc("Workspace", workspace_name)
		doc.update(ws_doc)
		doc.save(ignore_permissions=True)
		print(f"  ✔ Updated Workspace: {workspace_name}")

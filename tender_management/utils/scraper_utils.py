# tender_management/utils/scraper_utils.py
import frappe
import subprocess
import os

@frappe.whitelist()
def run_scraper_job(pages=None):
	"""
	Enqueues the scraper to run in the background.
	Uses a fully detached subprocess to bypass all Frappe/RQ timeouts.
	"""
	# Get default from settings if not provided
	if pages is None:
		settings = frappe.get_single("Tender Scraper Settings")
		pages = settings.page_limit or 80

	frappe.logger().info(f"Scraper job requested for {pages} pages")
	try:
		# Path to the bench CLI
		bench_path = "/usr/local/bin/bench"
		
		# Command to run the scraper via bench execute
		# Use start_crawling_direct which handles the Scrapy process
		cmd = [
			bench_path, 
			"--site", frappe.local.site, 
			"execute", "tender_management.utils.scraper_utils.start_crawling_direct", 
			"--kwargs", f'{{"pages": {pages}}}'
		]
		
		# Execute as a completely detached background process
		log_path = "/home/frappe/frappe-bench/logs/tender_scraper.log"
		with open(log_path, "a") as f:
			f.write(f"\n--- Starting scraper job for {pages} pages ---\n")
		
		subprocess.Popen(
			cmd, 
			stdout=open(log_path, "a"), 
			stderr=subprocess.STDOUT, 
			start_new_session=True
		)
		
		return {"status": "success", "message": "Scraping job started in the background. Please wait a few minutes for results to appear."}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Scraper Job Launcher Error")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def start_crawling_direct(pages=80):
	"""
	Initializes and runs the Scrapy spider directly.
	This is called by the background bench process.
	"""
	try:
		from scrapy.crawler import CrawlerProcess
		from scrapy.settings import Settings
		from tender_management.scrapers.merkato_spider import MerkatoSpider
		
		settings = Settings()
		settings.set('BOT_NAME', 'merkato_bot')
		settings.set('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
		settings.set('LOG_LEVEL', 'INFO')
		settings.set('REQUEST_FINGERPRINTER_IMPLEMENTATION', '2.7')
		settings.set('DOWNLOAD_DELAY', 1.5)
		settings.set('AUTOTHROTTLE_ENABLED', True)
		
		# Increase log level slightly for cleaner background runs
		process = CrawlerProcess(settings)
		process.crawl(MerkatoSpider, page_limit=int(pages))
		process.start() 
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Scraper Execution Error")

@frappe.whitelist()
def sync_categories():
	"""
	Fetches categories from 2merkato and populates Merkato Category DocType.
	Uses multiple strategies for maximum coverage.
	"""
	import requests
	import json
	import html
	from bs4 import BeautifulSoup
	
	try:
		# Strategy 1: Main Tenders Page
		url = "https://tender.2merkato.com/tenders"
		headers = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
		}
		r = requests.get(url, headers=headers, timeout=30)
		soup = BeautifulSoup(r.text, "html.parser")
		
		categories = set()
		
		# Try Inertia JSON state
		app_div = soup.find("div", id="app")
		if app_div and app_div.get("data-page"):
			try:
				data = json.loads(html.unescape(app_div.get("data-page")))
				props = data.get("props", {})
				
				def extract_categories(obj):
					if isinstance(obj, dict):
						for k, v in obj.items():
							if "categor" in k.lower() and isinstance(v, list):
								for item in v:
									name = None
									if isinstance(item, dict):
										name = item.get("name_en") or item.get("name")
									elif isinstance(item, str):
										name = item
									if name: categories.add(name.strip())
							extract_categories(v)
					elif isinstance(obj, list):
						for item in obj:
							extract_categories(item)
				
				extract_categories(props)
			except Exception:
				pass

		# Try Ant Design Tree titles
		titles = soup.find_all("span", class_="ant-tree-title")
		for t in titles:
			inner_span = t.find("span", title=True)
			name = inner_span.get("title") if inner_span else t.get_text()
			if name and len(name.strip()) > 2:
				categories.add(name.strip())
		
		# Strategy 2: Check standard industry list if nothing found
		if len(categories) < 10:
			standard_cats = [
				"Accounting and Auditing, Accounting System Design", "Advertising and Promotion", 
				"Agriculture and Farming", "Air conditioning and Refrigeration", "Art", 
				"Banking Equipment and Services", "Catering and Cafeteria Services", 
				"Chemicals and Reagents", "Cleaning and Janitorial Equipment and Service", 
				"Construction and Water Works", "Consultancy", "Consumable Goods", 
				"Courier Services", "Education and Training", 
				"Electrical, Electromechanical and Electronics", "Energy, Power and Electricity", 
				"Food and Beverage", "Food Items and Drinks", "Fuel and Lubricants", 
				"Furniture and Furnishing", "Gardening and Landscaping", "General Service Provision", 
				"Geotechnical Investigation & Laboratory Testing", "Government Treasury Bill", 
				"Hand Tools and Workshop Equipment", "Health Care, Medical Industry", 
				"Hospitality, Tour and Travel", "Humanitarian Aid Supply, Relief Items", 
				"IT and Telecom", "Kitchen Equipment", "Laboratory Equipment and Chemicals", 
				"Labour Outsourcing Services", "Land Lease & Real Estate", "Maintenance and Repair", 
				"Mechanical", "Metal and Metal Working", "Office Supplies and Services", 
				"Software Supply and Development and Web Design", "Vehicles and Spare Parts"
			]
			for sc in standard_cats:
				categories.add(sc)

		count = 0
		for cat_name in sorted(list(categories)):
			if not frappe.db.exists("Merkato Category", cat_name):
				doc = frappe.new_doc("Merkato Category")
				doc.category_name = cat_name
				doc.insert(ignore_permissions=True)
				count += 1
		
		frappe.db.commit()
		return {"status": "success", "count": count, "total": len(categories)}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Category Sync Error")
		return {"status": "error", "message": "Failed to sync categories. Check Error Log."}

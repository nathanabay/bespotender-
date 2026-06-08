# tender_management/utils/scraper_utils.py
import frappe
import subprocess
import os
import json
import html
from bs4 import BeautifulSoup

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
		cmd = [
			bench_path, 
			"--site", frappe.local.site, 
			"execute", "tender_management.utils.scraper_utils.start_crawling_direct", 
			"--kwargs", f'{{"pages": {pages}}}'
		]
		
		# Execute as a completely detached background process
		log_path = "/tmp/tender_scraper.log"
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
		
		process = CrawlerProcess(settings)
		process.crawl(MerkatoSpider, page_limit=int(pages))
		process.start() 
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Scraper Execution Error")

@frappe.whitelist()
def sync_categories():
	"""
	Fetches categories and subcategories from 2merkato.
	Reconstructs the hierarchy based on indentation levels.
	"""
	import requests
	
	try:
		# Attempt live scrape first
		url = "https://tender.2merkato.com/tenders"
		headers = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
		}
		r = requests.get(url, headers=headers, timeout=30)
		soup = BeautifulSoup(r.text, "html.parser")
		tree_nodes = soup.find_all("div", class_="ant-tree-treenode")
		
		if not tree_nodes:
			# Fallback: Check for local tenderdesc.html file
			local_file = "/home/frappe/frappe-bench/apps/tender_management/tenderdesc.html"
			if os.path.exists(local_file):
				with open(local_file, "r") as f:
					soup = BeautifulSoup(f.read(), "html.parser")
					tree_nodes = soup.find_all("div", class_="ant-tree-treenode")

		if not tree_nodes:
			return {"status": "error", "message": "Could not find categories in tree structure."}

		level_stack = {}
		count = 0
		
		for node in tree_nodes:
			indent = len(node.find_all("span", class_="ant-tree-indent-unit"))
			title_span = node.find("span", class_="ant-tree-title")
			if not title_span: continue
			
			inner = title_span.find("span", title=True)
			name = inner.get("title") if inner else title_span.get_text()
			name = name.strip()
			
			if not name or name == "N/A": continue
			
			parent = level_stack.get(indent - 1) if indent > 0 else None
			is_group = bool(node.find("span", class_="ant-tree-switcher_close") or 
						   node.find("span", class_="ant-tree-switcher_open"))
			
			if not frappe.db.exists("Merkato Category", name):
				doc = frappe.new_doc("Merkato Category")
				doc.category_name = name
				doc.is_group = 1 if is_group else 0
				doc.parent_category = parent
				doc.insert(ignore_permissions=True)
				count += 1
			else:
				frappe.db.set_value("Merkato Category", name, {
					"is_group": 1 if is_group else 0,
					"parent_category": parent
				})
			
			level_stack[indent] = name
		
		frappe.db.commit()
		total_count = frappe.db.count("Merkato Category")
		return {
			"status": "success", 
			"new_count": count, 
			"total_count": total_count,
			"message": f"Successfully synced categories. {total_count} categories are now available."
		}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Category Sync Error")
		return {"status": "error", "message": "An error occurred during category sync."}

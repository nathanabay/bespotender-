# tender_management/utils/scraper_utils.py
import frappe
import subprocess
import os
import json
import html
from bs4 import BeautifulSoup

def _get_bench_path():
	"""Dynamically locate the bench executable."""
	import shutil
	return shutil.which("bench") or "/usr/local/bin/bench"

def _get_log_path():
	"""Return a site-specific log path instead of a shared /tmp file."""
	site_path = frappe.get_site_path()
	return os.path.join(site_path, "logs", "tender_scraper.log")

@frappe.whitelist()
def run_scraper_job(pages=None):
	"""
	Enqueues the scraper to run in the background.
	Uses a fully detached subprocess to bypass all Frappe/RQ timeouts.
	Checks for an already-running instance before starting a new one.
	"""
	if not frappe.has_permission("Tender Scraper Settings", "write"):
		frappe.throw(frappe._("Not permitted to launch scraper jobs"), frappe.PermissionError)

	# Prevent overlapping runs
	try:
		check = subprocess.run(
			["pgrep", "-f", "start_crawling_direct"],
			capture_output=True, text=True, timeout=5
		)
		if check.returncode == 0:
			return {"status": "already_running", "message": "A scraper job is already running. Please wait for it to finish."}
	except (subprocess.TimeoutExpired, FileNotFoundError):
		pass  # pgrep not available or timed out; proceed cautiously

	if pages is None:
		settings = frappe.get_single("Tender Scraper Settings")
		pages = settings.page_limit or 80

	frappe.logger().info(f"Scraper job requested for {pages} pages")
	try:
		bench_path = _get_bench_path()
		cmd = [
			bench_path,
			"--site", frappe.local.site,
			"execute", "tender_management.utils.scraper_utils.start_crawling_direct",
			"--kwargs", json.dumps({"pages": int(pages)})
		]

		log_path = _get_log_path()
		os.makedirs(os.path.dirname(log_path), exist_ok=True)
		with open(log_path, "a") as f:
			f.write(f"\n--- Starting scraper job for {pages} pages ---\n")

		env = os.environ.copy()
		env["PYTHONUNBUFFERED"] = "1"

		subprocess.Popen(
			cmd,
			stdout=open(log_path, "a"),
			stderr=subprocess.STDOUT,
			start_new_session=True,
			env=env
		)

		return {"status": "success", "message": "Scraping job started in the background. Please wait a few minutes for results to appear."}
	except (OSError, ValueError) as e:
		frappe.log_error(frappe.get_traceback(), "Scraper Job Launcher Error")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def start_crawling_direct(pages=80):
	"""
	Initializes and runs the Scrapy spider directly.
	This is called by the background bench process.
	"""
	if not frappe.has_permission("Tender Scraper Settings", "write"):
		frappe.throw(frappe._("Not permitted to execute crawler directly"), frappe.PermissionError)
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
	The live HTTP fetch is enqueued as a background job to avoid blocking the web worker.
	"""
	if not frappe.has_permission("Tender Scraper Settings", "write"):
		frappe.throw(frappe._("Not permitted to sync categories"), frappe.PermissionError)

	frappe.enqueue(
		"tender_management.utils.scraper_utils._sync_categories_background",
		queue="short",
		timeout=120
	)
	return {"status": "queued", "message": "Category sync has been queued. Results will be available shortly."}

def _sync_categories_background():
	"""Background worker for category sync. Not exposed as a whitelisted endpoint."""
	import requests
	try:
		soup = None
		try:
			url = "https://tender.2merkato.com/tenders"
			headers = {
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
			}
			r = requests.get(url, headers=headers, timeout=10)
			r.raise_for_status()
			soup = BeautifulSoup(r.text, "html.parser")
		except requests.RequestException as e:
			frappe.logger().warning(f"Category Sync: Live fetch failed, using fallback: {str(e)}")

		tree_nodes = None
		if soup:
			tree_nodes = soup.find_all("div", class_="ant-tree-treenode")

		if not tree_nodes:
			# Fallback: use a local cache file relative to the app path
			local_file = os.path.join(frappe.get_app_path("tender_management"), "..", "tenderdesc.html")
			local_file = os.path.normpath(local_file)
			if os.path.exists(local_file):
				with open(local_file, "r") as f:
					soup = BeautifulSoup(f.read(), "html.parser")
					tree_nodes = soup.find_all("div", class_="ant-tree-treenode")

		if not tree_nodes:
			frappe.log_error("Could not find categories in tree structure.", "Category Sync")
			return

		level_stack = {}
		count = 0

		for node in tree_nodes:
			indent = len(node.find_all("span", class_="ant-tree-indent-unit"))
			title_span = node.find("span", class_="ant-tree-title")
			if not title_span:
				continue

			inner = title_span.find("span", title=True)
			name = inner.get("title") if inner else title_span.get_text()
			name = name.strip()

			if not name or name == "N/A":
				continue

			parent = level_stack.get(indent - 1) if indent > 0 else None
			is_group = bool(
				node.find("span", class_="ant-tree-switcher_close") or
				node.find("span", class_="ant-tree-switcher_open")
			)

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

		# frappe.db.commit() is handled automatically at end of background job
		total_count = frappe.db.count("Merkato Category")
		frappe.logger().info(f"Category sync complete: {count} new, {total_count} total.")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Category Sync Background Error")

@frappe.whitelist()
def check_scraper_status():
	"""
	Checks if the scraper background process is currently running and returns the last few logs.
	"""
	if not frappe.has_permission("Tender Scraper Settings", "read"):
		frappe.throw(frappe._("Not permitted to check scraper status"), frappe.PermissionError)
	try:
		# Use pgrep (safe, no shell=True) to check for running scraper processes
		try:
			result = subprocess.run(
				["pgrep", "-f", "start_crawling_direct"],
				capture_output=True, text=True, timeout=5
			)
			is_running = result.returncode == 0
		except (subprocess.TimeoutExpired, FileNotFoundError):
			is_running = False

		logs = ""
		log_path = _get_log_path()
		if os.path.exists(log_path):
			try:
				if not os.access(log_path, os.R_OK):
					logs = "Error: Log file exists but is NOT READABLE by the web server."
				else:
					try:
						tail_result = subprocess.run(
							["tail", "-n", "20", log_path],
							capture_output=True, text=True, errors="ignore", timeout=5
						)
						logs = tail_result.stdout.strip()
					except (subprocess.TimeoutExpired, FileNotFoundError):
						pass

					if not logs:
						with open(log_path, "r", errors="ignore") as f:
							all_lines = f.readlines()
							logs = "".join(all_lines[-20:]).strip()

					if not logs:
						logs = "Log file found but it appears to be EMPTY."
			except OSError as e:
				logs = f"Error reading log file: {str(e)}"
		else:
			logs = f"Log file NOT FOUND at {log_path}."

		status_msg = "RUNNING" if is_running else "STOPPED"
		return {
			"status": "success",
			"is_running": is_running,
			"message": f"The scraper is currently {status_msg}.",
			"logs": logs
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Check Scraper Status Error")
		return {"status": "error", "message": f"Failed to check status: {str(e)}"}

@frappe.whitelist()
def stop_scraper_job():
	"""
	Gracefully stops any running Scrapy processes using SIGTERM, then SIGKILL only if needed.
	"""
	if not frappe.has_permission("Tender Scraper Settings", "write"):
		frappe.throw(frappe._("Not permitted to stop scraper jobs"), frappe.PermissionError)
	try:
		# Use SIGTERM first for graceful shutdown, not SIGKILL (-9)
		for pattern in ["start_crawling_direct", "merkato_bot"]:
			try:
				subprocess.run(
					["pkill", "-TERM", "-f", pattern],
					capture_output=True, timeout=10
				)
			except (subprocess.TimeoutExpired, FileNotFoundError) as e:
				frappe.logger().warning(f"pkill for {pattern} failed: {e}")
		frappe.logger().info("Scraper processes have been manually stopped.")
		return {"status": "success", "message": "All scraper processes have been stopped."}
	except OSError as e:
		frappe.log_error(frappe.get_traceback(), "Stop Scraper Error")
		return {"status": "error", "message": f"Failed to stop scraper: {str(e)}"}


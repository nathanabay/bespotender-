# tender_management/utils/run_scraper.py
import frappe
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from tender_management.scrapers.merkato_spider import MerkatoSpider

@frappe.whitelist()
def run_scraper_job():
	"""
	Enqueues the scraper to run in the background.
	This is called by the Frappe scheduler.
	"""
	try:
		# Enqueue the actual scraping process to avoid blocking the scheduler
		frappe.enqueue(
			"tender_management.utils.run_scraper.start_crawling", 
			is_async=True, 
			timeout=1800,
			job_name="Merkato Tender Scraper"
		)
		return {"status": "success", "message": "Scraping job has been enqueued."}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Scraper Job Enqueue Error")
		return {"status": "error", "message": str(e)}

def start_crawling():
	"""
	Initializes and runs the Scrapy spider.
	This runs in a background worker process.
	"""
	# We need to manually initialize the Scrapy settings since we are running 
	# a standalone script inside the Frappe context.
	settings = get_project_settings()
	
	# Optional: Disable standard logging to avoid clashing with Frappe if needed, 
	# but Scrapy's log is useful for debugging in the worker logs.
	# settings.set('LOG_ENABLED', False)

	process = CrawlerProcess(settings)
	process.crawl(MerkatoSpider)
	process.start() # This blocks until crawling is finished

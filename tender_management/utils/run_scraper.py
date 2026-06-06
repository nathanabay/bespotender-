# tender_management/utils/run_scraper.py
import frappe
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
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
			timeout=7200, # Increased to 2 hours for a full site scrape
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
	try:
		# Manually define Scrapy settings
		settings = Settings()
		settings.set('BOT_NAME', 'merkato_bot')
		settings.set('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
		settings.set('LOG_LEVEL', 'INFO')
		# Necessary for some environments
		settings.set('REQUEST_FINGERPRINTER_IMPLEMENTATION', '2.7')

		# Politeness settings to avoid 429 Rate Limiting
		settings.set('DOWNLOAD_DELAY', 1.0) # 1 second delay between requests
		settings.set('AUTOTHROTTLE_ENABLED', True)
		settings.set('AUTOTHROTTLE_START_DELAY', 1.0)
		settings.set('AUTOTHROTTLE_MAX_DELAY', 10.0)
		settings.set('AUTOTHROTTLE_TARGET_CONCURRENCY', 1.0)
		
		# CrawlerProcess is better for standalone execution in a worker
		process = CrawlerProcess(settings)
		process.crawl(MerkatoSpider)
		process.start() 
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Scraper Execution Error")

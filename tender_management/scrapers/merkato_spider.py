# tender_management/scrapers/merkato_spider.py
import scrapy
import json
import frappe
import html
from frappe.utils import get_datetime

class MerkatoSpider(scrapy.Spider):
	name = "merkato_tender"
	allowed_domains = ["tender.2merkato.com"]
	login_url = "https://tender.2merkato.com/login"
	start_urls = ["https://tender.2merkato.com/tenders"]

	def start_requests(self):
		yield scrapy.Request(self.login_url, callback=self.login)

	def login(self, response):
		"""
		Handles the login process using Scrapy's FormRequest to automatically
		handle CSRF tokens. Assumes standard 'email' and 'password' fields.
		"""
		username = frappe.conf.get("merkato_username")
		password = frappe.conf.get("merkato_password")

		if not username or not password:
			self.log("Merkato credentials missing from site_config.json. Scraping without login.", level=scrapy.log.WARNING)
			yield scrapy.Request(self.start_urls[0], callback=self.parse_tenders_page)
			return

		return scrapy.FormRequest.from_response(
			response,
			formdata={"email": username, "password": password},
			callback=self.after_login
		)

	def after_login(self, response):
		"""Verify login and proceed."""
		if "login" in response.url:
			self.log("Login failed. Check credentials.", level=scrapy.log.ERROR)
			return

		self.log("Login successful. Starting scrape.")
		yield scrapy.Request(self.start_urls[0], callback=self.parse_tenders_page)

	def parse_tenders_page(self, response):
		"""
		Extracts the JSON payload from the data-page attribute and parses it.
		"""
		# Extract the raw string from the data-page attribute
		data_page_raw = response.css("div#app::attr(data-page)").get()
		
		if not data_page_raw:
			self.log("Could not find data-page attribute. Site structure may have changed.", level=scrapy.log.ERROR)
			return

		# Unescape HTML entities (&quot; to ")
		data_page_str = html.unescape(data_page_raw)

		try:
			page_data = json.loads(data_page_str)
		except json.JSONDecodeError as e:
			self.log(f"Failed to parse JSON payload: {e}", level=scrapy.log.ERROR)
			return

		# Navigate the JSON structure based on the sample HTML analysis
		props = page_data.get("props", {})
		tenders_data = props.get("tenders", {})
		tenders_list = tenders_data.get("data", [])

		for tender in tenders_list:
			tender_id = tender.get("id")
			if tender_id:
				detail_url = f"https://tender.2merkato.com/tenders/{tender_id}"
				yield response.follow(
					detail_url, 
					self.parse_tender_details, 
					cb_kwargs={"list_data": tender}
				)

		# Pagination handling
		next_page_url = tenders_data.get("next_page_url")
		if next_page_url:
			yield response.follow(next_page_url, self.parse_tenders_page)

	def parse_tender_details(self, response, list_data):
		"""
		Extracts full details. Tries JSON payload first, falls back to CSS selectors 
		for the description if it's rendered server-side as raw HTML.
		"""
		data_page_raw = response.css("div#app::attr(data-page)").get()
		tender_details = {}
		if data_page_raw:
			data_page_str = html.unescape(data_page_raw)
			try:
				page_data = json.loads(data_page_str)
				tender_details = page_data.get("props", {}).get("tender", {}) 
			except json.JSONDecodeError:
				pass

		# Combine data from the list view and the detail view
		title = tender_details.get("title") or list_data.get("title", "N/A")
		
		# Extract category
		category_data = tender_details.get("category") or list_data.get("category")
		category = "N/A"
		if isinstance(category_data, dict):
			category = category_data.get("name_en", "N/A")
		elif isinstance(category_data, list) and category_data:
			 category = category_data[0].get("name_en", "N/A")
		elif isinstance(category_data, str):
			category = category_data

		# Extract Region
		region_data = tender_details.get("region") or list_data.get("region")
		region = "N/A"
		if isinstance(region_data, dict):
			region = region_data.get("name_en") or region_data.get("name") or "N/A"
		elif isinstance(region_data, str):
			region = region_data
		else:
			# Fallback CSS for Region
			region = response.css('div:contains("Region") + div a::text, div:contains("Region") + div::text').get(default="N/A").strip()

		closing_date_str = tender_details.get("bid_closing_date") or list_data.get("bid_closing_date")
		try:
			closing_date = get_datetime(closing_date_str) if closing_date_str else None
		except Exception:
			closing_date = None

		# HYBRID APPROACH: Handle description. 
		description = tender_details.get("description") or tender_details.get("content")
		if not description:
			# Fallback: Extract raw HTML content if the description wasn't in the JSON blob
			description_html = response.css('div.overflow-x-auto').get()
			description = description_html if description_html else "No description provided."

		# Extract AI Summary
		ai_summary = tender_details.get("ai_summary")
		if not ai_summary:
			# Fallback CSS for AI summary
			ai_summary_parts = response.css('div.mt-6.space-y-3.rounded-lg.border.p-6 h4:contains("AI Summary") ~ div::text').getall()
			ai_summary = " ".join([p.strip() for p in ai_summary_parts if p.strip()]) if ai_summary_parts else None

		# Extract Documents
		documents_list = []
		doc_links = response.css('div.bg-blue-50 a[href*="/documents/"]::attr(href)').getall()
		for doc_link in doc_links:
			documents_list.append(response.urljoin(doc_link))
		
		documents_str = "\n".join(documents_list) if documents_list else None

		if not frappe.db.exists("Scraped Tender", {"source_url": response.url}):
			doc = frappe.new_doc("Scraped Tender")
			doc.title = title.strip() if title else "N/A"
			doc.category = category
			doc.region = region
			doc.closing_date = closing_date
			doc.source_url = response.url
			doc.description = description
			doc.ai_summary = ai_summary
			doc.documents = documents_str
			doc.insert(ignore_permissions=True)
			frappe.db.commit() 
			self.log(f"Created new tender: {doc.title}")
		else:
			self.log(f"Tender already exists: {response.url}")

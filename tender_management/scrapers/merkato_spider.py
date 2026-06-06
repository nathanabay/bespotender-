# tender_management/scrapers/merkato_spider.py
import scrapy
import json
import frappe
import html
from frappe.utils import get_datetime

class MerkatoSpider(scrapy.Spider):
	name = "merkato_tender"
	start_urls = ["https://tender.2merkato.com/login"]
	handle_httpstatus_list = [422, 409]

	def parse(self, response):
		"""
		Entry point: extract CSRF token and handle login.
		"""
		# Extract data-page JSON
		data_page_raw = response.css("div#app::attr(data-page)").get()
		if not data_page_raw:
			self.logger.error("Could not find data-page on login page.")
			yield scrapy.Request("https://tender.2merkato.com/tenders", callback=self.parse_tenders_list)
			return

		data_page_str = html.unescape(data_page_raw)
		try:
			page_data = json.loads(data_page_str)
			csrf_token = page_data.get("props", {}).get("csrf_token")
			inertia_version = page_data.get("version")
		except Exception as e:
			self.logger.error(f"Failed to parse login page JSON: {e}")
			yield scrapy.Request("https://tender.2merkato.com/tenders", callback=self.parse_tenders_list)
			return

		username = frappe.conf.get("merkato_username")
		password = frappe.conf.get("merkato_password")
		
		if not username or not password:
			self.logger.warning("Merkato credentials missing in site_config.json. Scraping without login.")
			yield scrapy.Request("https://tender.2merkato.com/tenders", callback=self.parse_tenders_list)
			return

		self.logger.info(f"Attempting login for: {username}")
		
		# Perform an Inertia-style POST request
		yield scrapy.Request(
			"https://tender.2merkato.com/login",
			method="POST",
			headers={
				"X-Inertia": "true",
				"X-Inertia-Version": inertia_version,
				"X-CSRF-TOKEN": csrf_token,
				"Content-Type": "application/json",
				"Accept": "application/json",
			},
			body=json.dumps({
				"emailOrMobile": username, 
				"password": password,
				"remember": True
			}),
			callback=self.after_login,
			dont_filter=True
		)

	def after_login(self, response):
		"""Verify login and proceed."""
		if response.status == 422:
			self.logger.error(f"Login validation error: {response.text}")
		elif response.status == 409:
			self.logger.warning("Inertia version mismatch (409) during login. Proceeding anyway.")
		elif "login" in response.url:
			self.logger.error("Login failed (redirected back to login).")
		else:
			self.logger.info("Login successful.")
		
		yield scrapy.Request("https://tender.2merkato.com/tenders", callback=self.parse_tenders_list)

	def parse_tenders_list(self, response):
		"""
		Extracts the JSON payload from the data-page attribute and parses it.
		"""
		data_page_raw = response.css("div#app::attr(data-page)").get()
		
		if not data_page_raw:
			self.logger.error("Could not find data-page attribute on tenders list.")
			return

		data_page_str = html.unescape(data_page_raw)
		try:
			page_data = json.loads(data_page_str)
		except json.JSONDecodeError as e:
			self.logger.error(f"Failed to parse JSON: {e}")
			return

		props = page_data.get("props", {})
		tenders_data = props.get("tenders", {})
		tenders_list = tenders_data.get("data", [])

		self.logger.info(f"Found {len(tenders_list)} tenders in the list.")

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
		links = tenders_data.get("links", {})
		next_page = links.get("next")
		if next_page:
			self.logger.info(f"Following next page: {next_page}")
			yield response.follow(next_page, self.parse_tenders_list)

	def parse_tender_details(self, response, list_data):
		"""
		Extracts full details.
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

		title = tender_details.get("title") or list_data.get("title", "N/A")
		# Extract category
		category_data = tender_details.get("categories") or tender_details.get("category") or \
						list_data.get("categories") or list_data.get("category")
		category = "N/A"
		if isinstance(category_data, list) and category_data:
			# Get names from all categories if multiple
			names = [c.get("name_en") for c in category_data if isinstance(c, dict) and c.get("name_en")]
			category = ", ".join(names) if names else "N/A"
		elif isinstance(category_data, dict):
			category = category_data.get("name_en", "N/A")
		elif isinstance(category_data, str):
			category = category_data


		region_data = tender_details.get("region") or list_data.get("region")
		region = "N/A"
		if isinstance(region_data, dict):
			region = region_data.get("name_en") or region_data.get("name") or "N/A"
		elif isinstance(region_data, str):
			region = region_data
		else:
			region_sel = response.css('div:contains("Region") + div a::text, div:contains("Region") + div::text').get()
			region = region_sel.strip() if region_sel else "N/A"

		closing_date_str = tender_details.get("bid_closing_date") or list_data.get("bid_closing_date")
		try:
			closing_date = get_datetime(closing_date_str) if closing_date_str else None
		except Exception:
			closing_date = None

		description = tender_details.get("description") or tender_details.get("content")
		if not description:
			description_html = response.css('div.overflow-x-auto').get()
			description = description_html if description_html else "No description provided."

		ai_summary = tender_details.get("ai_summary")
		if not ai_summary:
			ai_summary_parts = response.css('div.mt-6.space-y-3.rounded-lg.border.p-6 h4:contains("AI Summary") ~ div::text').getall()
			ai_summary = " ".join([p.strip() for p in ai_summary_parts if p.strip()]) if ai_summary_parts else None

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
			self.logger.info(f"Created new tender: {doc.title[:50]}...")
		else:
			self.logger.debug(f"Tender already exists: {response.url}")

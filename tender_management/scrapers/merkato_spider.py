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
	page_count = 0

	def __init__(self, page_limit=None, *args, **kwargs):
		super(MerkatoSpider, self).__init__(*args, **kwargs)
		
		# Load settings from Frappe
		self.settings_doc = frappe.get_single("Tender Scraper Settings")
		
		# Set page limit
		if page_limit:
			self.page_limit = int(page_limit)
		else:
			self.page_limit = int(self.settings_doc.page_limit or 80)
			
		# Load enabled categories
		self.enabled_categories = [c.category_name.strip().lower() for c in self.settings_doc.categories if c.enabled]
		
		print(f"--- MerkatoSpider initialized ---")
		print(f"--- Page Limit: {self.page_limit} ---")
		print(f"--- Filter: OPEN Tenders Only ---")
		if self.enabled_categories:
			print(f"--- Filter Categories: {', '.join(self.enabled_categories)} ---")
		else:
			print(f"--- Filter Categories: ALL ---")

	def parse(self, response):
		"""
		Entry point: handle login.
		"""
		print(f"--- Entry point: {response.url} ---")
		
		if "/tenders" in response.url:
			return self.parse_tenders_list(response)

		data_page_raw = response.css("div#app::attr(data-page)").get()
		if not data_page_raw:
			# Fallback: go to tenders page with open status
			yield scrapy.Request("https://tender.2merkato.com/tenders?status=open", callback=self.parse_tenders_list)
			return

		data_page_str = html.unescape(data_page_raw)
		try:
			page_data = json.loads(data_page_str)
			csrf_token = page_data.get("props", {}).get("csrf_token")
			inertia_version = page_data.get("version")
		except Exception:
			yield scrapy.Request("https://tender.2merkato.com/tenders?status=open", callback=self.parse_tenders_list)
			return

		username = self.settings_doc.merkato_username
		password = self.settings_doc.get_password("merkato_password")
		
		if not username or not password:
			print("--- Error: Credentials missing. Proceeding without login. ---")
			yield scrapy.Request("https://tender.2merkato.com/tenders?status=open", callback=self.parse_tenders_list)
			return

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
		"""Verify login and proceed to OPEN tenders."""
		if response.status == 409:
			location = response.headers.get("X-Inertia-Location")
			if location:
				location_str = location.decode('utf-8')
				yield scrapy.Request(response.urljoin(location_str), callback=self.parse_tenders_list)
				return

		# Direct to OPEN tenders only
		yield scrapy.Request("https://tender.2merkato.com/tenders?status=open", callback=self.parse_tenders_list)

	def parse_tenders_list(self, response):
		"""
		Extracts OPEN tenders from the JSON payload.
		"""
		self.page_count += 1
		print(f"--- Parsing tenders page {self.page_count}: {response.url} ---")

		data_page_raw = response.css("div#app::attr(data-page)").get()
		if not data_page_raw: return

		try:
			page_data = json.loads(html.unescape(data_page_raw))
		except Exception: return

		props = page_data.get("props", {})
		tenders_data = props.get("tenders", {})
		tenders_list = tenders_data.get("data", [])

		for tender in tenders_list:
			# --- HARD FILTER: MUST BE OPEN ---
			if not tender.get("is_open"):
				continue

			tender_id = tender.get("id")
			if tender_id:
				detail_url = f"https://tender.2merkato.com/tenders/{tender_id}"
				yield response.follow(
					detail_url, 
					self.parse_tender_details, 
					cb_kwargs={"list_data": tender}
				)

		# Pagination
		if self.page_count < self.page_limit:
			links = tenders_data.get("links", {})
			next_page = links.get("next")
			if next_page:
				yield response.follow(next_page, self.parse_tenders_list)

	def parse_tender_details(self, response, list_data):
		"""
		Extracts full details and saves to Frappe.
		"""
		data_page_raw = response.css("div#app::attr(data-page)").get()
		tender_details = {}
		if data_page_raw:
			try:
				page_data = json.loads(html.unescape(data_page_raw))
				tender_details = page_data.get("props", {}).get("tender", {}) 
			except Exception: pass

		# --- RE-VERIFY OPEN STATUS ---
		# Check JSON flags
		is_open = tender_details.get("is_open", list_data.get("is_open"))
		status_str = tender_details.get("status", list_data.get("status", "")).lower()
		
		if is_open is False or status_str == "closed":
			self.logger.debug(f"Skipping closed tender (JSON flag): {response.url}")
			return
			
		# Check raw HTML for "Bidding closed" badges just in case JSON is misleading
		if "bidding closed" in response.text.lower():
			self.logger.debug(f"Skipping closed tender (HTML badge): {response.url}")
			return

		original_title = (tender_details.get("title") or list_data.get("title", "N/A")).strip()
		truncated_title = original_title[:140].strip()
		
		# Category
		category_data = tender_details.get("categories") or tender_details.get("category") or \
						list_data.get("categories") or list_data.get("category")
		category = "N/A"
		if isinstance(category_data, list) and category_data:
			names = [c.get("name_en") or c.get("name") for c in category_data if isinstance(c, dict)]
			category = ", ".join([n for n in names if n]) or "N/A"
		elif isinstance(category_data, dict):
			category = category_data.get("name_en") or category_data.get("name") or "N/A"
		elif isinstance(category_data, str):
			category = category_data

		# Category Filtering
		if self.enabled_categories:
			match = False
			# Normalize tender categories: lowercase, remove extra spaces
			tender_cats_raw = category.split(",")
			tender_cats = [c.strip().lower() for c in tender_cats_raw]
			
			for ec in self.enabled_categories:
				ec_clean = ec.strip().lower()
				# Check for direct exact match
				if ec_clean in tender_cats:
					match = True
					break
			if not match: return

		# Region
		region_data = tender_details.get("region") or list_data.get("region")
		region = "N/A"
		if isinstance(region_data, dict):
			region = region_data.get("name_en") or region_data.get("name") or "N/A"
		elif isinstance(region_data, str):
			region = region_data
		else:
			region_sel = response.xpath('//div[contains(text(), "Region")]/following-sibling::div//text()').get()
			region = region_sel.strip() if region_sel else "N/A"

		# Metadata
		closing_date_str = tender_details.get("bid_closing_date") or list_data.get("bid_closing_date")
		try:
			closing_date = get_datetime(closing_date_str) if closing_date_str else None
		except Exception:
			closing_date = None

		closing_date_text = tender_details.get("bid_closing_date_text") or list_data.get("bid_closing_date_text")
		
		posted_date_raw = tender_details.get("created_at") or list_data.get("created_at")
		if posted_date_raw and "T" in posted_date_raw:
			posted_date = posted_date_raw.split("T")[0] + " " + posted_date_raw.split("T")[1][:8]
		else:
			posted_date = posted_date_raw
			
		doc_price = tender_details.get("bid_document_price") or list_data.get("bid_document_price")
		bid_bond = tender_details.get("bid_bond") or list_data.get("bid_bond")

		sources = tender_details.get("sources") or list_data.get("sources")
		published_on = "N/A"
		if isinstance(sources, list) and sources:
			source_list = []
			for s in sources:
				if isinstance(s, dict):
					name = s.get("name_en") or s.get("name")
					date = s.get("publication_date")
					source_list.append(f"{name} ({date})" if date else name)
			published_on = ", ".join(source_list) if source_list else "N/A"

		description = tender_details.get("description") or tender_details.get("content")
		if not description:
			description_html = response.css('div.overflow-x-auto').get()
			description = description_html if description_html else "No description provided."

		ai_summary = tender_details.get("ai_summary")
		if not ai_summary:
			ai_summary_parts = response.xpath('//h4[contains(text(), "AI Summary")]/following-sibling::div//text()').getall()
			ai_summary = " ".join([p.strip() for p in ai_summary_parts if p.strip()]) if ai_summary_parts else None

		documents_list = []
		doc_links = response.css('div.bg-blue-50 a[href*="/documents/"]::attr(href)').getall()
		for doc_link in doc_links:
			documents_list.append(response.urljoin(doc_link))
		documents_str = "\n".join(documents_list) if documents_list else None

		# Save to Frappe
		if not frappe.db.exists("Scraped Tender", truncated_title):
			try:
				doc = frappe.new_doc("Scraped Tender")
				doc.title = truncated_title
				doc.tender_title = original_title
				doc.category = category
				doc.region = region
				doc.posted_date = str(posted_date) if posted_date else None
				doc.published_on = published_on
				doc.closing_date = closing_date
				doc.closing_date_text = closing_date_text
				doc.bid_document_price = str(doc_price) if doc_price else None
				doc.bid_bond = str(bid_bond) if bid_bond else None
				doc.source_url = response.url
				doc.description = description
				doc.ai_summary = ai_summary
				doc.documents = documents_str
				doc.insert(ignore_permissions=True)
				frappe.db.commit() 
				print(f"--- Created tender: {truncated_title[:30]}... ---")
			except Exception as e:
				print(f"--- Error creating tender: {e} ---")

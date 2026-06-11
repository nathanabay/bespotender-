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

	def __init__(self, page_limit=None, username=None, password=None, enabled_categories=None, existing_titles=None, *args, **kwargs):
		super(MerkatoSpider, self).__init__(*args, **kwargs)
		
		# Set page limit
		self.page_limit = int(page_limit) if page_limit else 80
		self.username = username
		self.password = password
		self.enabled_categories = enabled_categories or []
		
		self.existing_titles = set(existing_titles or [])
		
		self.logger.info(f"MerkatoSpider initialized — Page Limit: {self.page_limit}")
		self.logger.info(f"Found {len(self.existing_titles)} existing tenders in cache")
		self.logger.info("Filter: OPEN Tenders Only")
		if self.enabled_categories:
			self.logger.info(f"Filter Categories: {', '.join(self.enabled_categories)}")
		else:
			self.logger.info("Filter Categories: ALL")

	def _get_fallback(self, key, primary_dict, fallback_dict, alt_key=None):
		val = primary_dict.get(key)
		if not val and alt_key:
			val = primary_dict.get(alt_key)
		if not val:
			val = fallback_dict.get(key)
		if not val and alt_key:
			val = fallback_dict.get(alt_key)
		return val

	def parse(self, response):
		"""
		Entry point: handle login.
		"""
		self.logger.info(f"--- Entry point: {response.url} ---")
		
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
		except json.JSONDecodeError:
			yield scrapy.Request("https://tender.2merkato.com/tenders?status=open", callback=self.parse_tenders_list)
			return

		username = self.username
		password = self.password
		
		if not username or not password:
			self.logger.info("--- Error: Credentials missing. Proceeding without login. ---")
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
		self.logger.info(f"--- Parsing tenders page {self.page_count}: {response.url} ---")

		data_page_raw = response.css("div#app::attr(data-page)").get()
		if not data_page_raw: return

		try:
			page_data = json.loads(html.unescape(data_page_raw))
		except json.JSONDecodeError: return

		props = page_data.get("props", {})
		tenders_data = props.get("tenders", {})
		tenders_list = tenders_data.get("data", [])
		
		if not tenders_list:
			self.logger.info("--- No tenders found on this page. Stopping. ---")
			return

		new_tenders_found = 0
		for tender in tenders_list:
			# --- HARD FILTER: MUST BE OPEN ---
			if not tender.get("is_open"):
				continue

			original_title = (tender.get("title") or "N/A").strip()
			truncated_title = original_title[:140].strip()

			# Lightning-fast cache check
			if truncated_title in self.existing_titles:
				self.logger.debug(f"Skipping already scraped tender (cached): {truncated_title[:30]}...")
				continue
			
			new_tenders_found += 1
			tender_id = tender.get("id")
			if tender_id:
				detail_url = f"https://tender.2merkato.com/tenders/{tender_id}"
				yield response.follow(
					detail_url, 
					self.parse_tender_details, 
					cb_kwargs={"list_data": tender}
				)

		# AUTO-STOP LOGIC: If we found ZERO new tenders on this entire page, 
		# it means we have reached the point where we've already scraped everything.
		if new_tenders_found == 0 and len(tenders_list) > 0:
			self.logger.info(f"--- Page {self.page_count} had 0 new tenders. Stopping spider early to save time. ---")
			return

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
			except json.JSONDecodeError: pass

		# --- RE-VERIFY OPEN STATUS ---
		# Check JSON flags
		is_open = tender_details.get("is_open", list_data.get("is_open"))
		status_str = tender_details.get("status", list_data.get("status", "")).lower()
		
		if is_open is False or status_str == "closed":
			self.logger.info(f"--- Skipping closed tender (JSON flag: is_open={is_open}, status={status_str}): {response.url} ---")
			return

		original_title = self._get_fallback("title", tender_details, list_data) or "N/A"
		original_title = original_title.strip()
		truncated_title = original_title[:140].strip()
		
		# Category
		category_data = self._get_fallback("categories", tender_details, list_data, alt_key="category")
		
		tender_cats_list = []
		if isinstance(category_data, list) and category_data:
			tender_cats_list = [c.get("name_en") or c.get("name") for c in category_data if isinstance(c, dict)]
			tender_cats_list = [n for n in tender_cats_list if n]
		elif isinstance(category_data, dict):
			cat_val = category_data.get("name_en") or category_data.get("name")
			if cat_val: tender_cats_list = [cat_val]
		elif isinstance(category_data, str):
			tender_cats_list = [category_data]

		category = ", ".join(tender_cats_list) if tender_cats_list else "N/A"
		
		self.logger.info(f"DEBUG: Tender '{truncated_title[:30]}' Cats: {tender_cats_list}")

		# Category Filtering
		if self.enabled_categories:
			match = False
			# Normalize tender categories: lowercase, remove extra spaces
			tender_cats = [c.strip().lower() for c in tender_cats_list]
			
			for ec in self.enabled_categories:
				ec_clean = ec.strip().lower()
				# Check for direct exact match
				if ec_clean in tender_cats:
					match = True
					break
			if not match: return

		# Region
		region_data = self._get_fallback("region", tender_details, list_data)
		region = "N/A"
		if isinstance(region_data, dict):
			region = region_data.get("name_en") or region_data.get("name") or "N/A"
		elif isinstance(region_data, str):
			region = region_data
		else:
			region_sel = response.xpath('//div[contains(text(), "Region")]/following-sibling::div//text()').get()
			region = region_sel.strip() if region_sel else "N/A"

		# Metadata
		closing_date_str = self._get_fallback("bid_closing_date", tender_details, list_data)
		try:
			closing_date = get_datetime(closing_date_str) if closing_date_str else None
		except ValueError:
			closing_date = None

		closing_date_text = self._get_fallback("bid_closing_date_text", tender_details, list_data)
		
		posted_date_raw = self._get_fallback("created_at", tender_details, list_data)
		if posted_date_raw and "T" in posted_date_raw:
			posted_date = posted_date_raw.split("T")[0] + " " + posted_date_raw.split("T")[1][:8]
		else:
			posted_date = posted_date_raw
			
		# Calculate days remaining
		days_remaining = 0
		if closing_date:
			from frappe.utils import now_datetime
			diff = closing_date - now_datetime()
			days_remaining = max(0, diff.days)

		doc_price = self._get_fallback("bid_document_price", tender_details, list_data)
		bid_bond = self._get_fallback("bid_bond", tender_details, list_data)

		sources = self._get_fallback("sources", tender_details, list_data)
		published_on = "N/A"
		if isinstance(sources, list) and sources:
			source_list = []
			for s in sources:
				if isinstance(s, dict):
					name = s.get("name_en") or s.get("name")
					date = s.get("publication_date")
					source_list.append(f"{name} ({date})" if date else name)
			published_on = ", ".join(source_list) if source_list else "N/A"

		description = self._get_fallback("description", tender_details, list_data, alt_key="content")
		if not description:
			description_html = response.css('div.overflow-x-auto').get()
			description = description_html if description_html else "No description provided."

		description = frappe.utils.sanitize_html(description)

		ai_summary = self._get_fallback("ai_summary", tender_details, list_data)
		if not ai_summary:
			ai_summary_parts = response.xpath('//h4[contains(text(), "AI Summary")]/following-sibling::div//text()').getall()
			ai_summary = " ".join([p.strip() for p in ai_summary_parts if p.strip()]) if ai_summary_parts else None

		if ai_summary:
			ai_summary = frappe.utils.sanitize_html(ai_summary)

		documents_list = []
		doc_links = response.css('div.bg-blue-50 a[href*="/documents/"]::attr(href)').getall()
		for doc_link in doc_links:
			documents_list.append(response.urljoin(doc_link))
		documents_str = "\n".join(documents_list) if documents_list else None
		
		# Company
		company_data = self._get_fallback("company", tender_details, list_data)
		company_name = "N/A"
		if isinstance(company_data, dict):
			company_name = company_data.get("name_en") or company_data.get("name") or "N/A"
		elif isinstance(company_data, str):
			company_name = company_data

		# Save to Frappe
		if not frappe.db.exists("Scraped Tender", truncated_title):
			try:
				doc = frappe.new_doc("Scraped Tender")
				doc.title = truncated_title
				doc.tender_title = original_title
				doc.company = company_name
				doc.category = category
				doc.region = region
				doc.posted_date = str(posted_date) if posted_date else None
				doc.published_on = published_on
				doc.closing_date = closing_date
				doc.days_remaining = days_remaining
				doc.closing_date_text = closing_date_text
				doc.bid_document_price = str(doc_price) if doc_price else None
				doc.bid_bond = str(bid_bond) if bid_bond else None
				doc.source_url = response.url
				doc.description = description
				doc.ai_summary = ai_summary
				doc.documents = documents_str
				doc.insert()
				frappe.db.commit() 
				self.logger.info(f"--- Created tender: {truncated_title[:30]}... ---")
			except frappe.exceptions.FrappeException as e:
				self.logger.error(f"--- Error creating tender: {e} ---")

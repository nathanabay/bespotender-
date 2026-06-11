# Deep Audit Report: Tender Management Codebase

**Date:** June 11, 2026
**Scope:** Deep Architectural and Security Audit via 10 Specialized Subagents
**Status:** Audit Complete. Awaiting User Confirmation for Remediation.

---

## 🔴 Critical Risk

### 1. SSRF and Local File Inclusion (LFI) via PDF Generation
- **Files:** `tender_management/utils/tender_doc_gen.py` (Lines 36-50), `tender_management/tender_management/doctype/document_template/document_template.py` (Lines 41-49)
- **Description:** The `@frappe.whitelist()` API `download_pdf` takes raw HTML directly from user input and passes it to Frappe's `get_pdf()`. Attackers can supply HTML containing `iframe` or `<script>` tags to extract local system files (e.g., `file:///etc/passwd`) or perform Server-Side Request Forgery.
- **Remediation:** Sanitize HTML input before rendering. Never accept raw HTML from the client to be rendered on the server side via `wkhtmltopdf`.

### 2. Stored XSS via Scraper Input
- **File:** `tender_management/scrapers/merkato_spider.py` (Lines 277-278, 316)
- **Description:** Raw HTML extracted from external sites is stored directly in the `Scraped Tender` description without sanitization, leading to Stored XSS when viewed in the Frappe UI.
- **Remediation:** Strip and sanitize raw HTML using a robust sanitization library (like `bleach`) before storing it in the database.

### 3. Transaction State Breakage and API Blocking (PDF Generation)
- **File:** `tender_management/utils/tender_doc_gen.py` (Line 100, 162-268)
- **Description:** Executing `frappe.db.commit()` inside a whitelisted HTTP request permanently corrupts data if subsequent PDF generation fails. Furthermore, synchronous generation blocks the web thread, causing 504 Gateway Timeouts.
- **Remediation:** Remove `frappe.db.commit()` to maintain atomic transactions. Move long-running synchronous PDF compilation tasks to Frappe background jobs via `frappe.enqueue`.

### 4. Security Check Bypass via Monkey Patching
- **File:** `tender_management/hooks.py` (Lines 14-26)
- **Description:** The core Frappe security function `pdf_contains_js` is monkey-patched to catch all exceptions and silently return `False`, allowing attackers to upload malformed PDFs that bypass JavaScript execution checks.
- **Remediation:** Remove the `pdf_contains_js` monkey patch. Handle exceptions gracefully without bypassing core security mechanisms.

### 5. Path Traversal / Arbitrary File Overwrite
- **File:** `tender_management/utils/docx_converter.py` (Lines 24-31)
- **Description:** `file_doc.file_name` is concatenated directly into a path (`os.path.join(temp_dir, file_name)`). An attacker can craft a filename with traversal sequences (`../../`) to overwrite arbitrary files on the system.
- **Remediation:** Use `os.path.basename(file_name)` or Frappe utilities to sanitize filenames before constructing system paths.

### 6. Unauthenticated Data Exposure (Public API Access)
- **File:** `tender_management/tender_management/doctype/scraped_tender/scraped_tender.json` (Lines 170-180)
- **Description:** The `Scraped Tender` doctype explicitly assigns the `All` role with `read` permissions. Unauthenticated `Guest` users can dump the entire database via the REST API.
- **Remediation:** Remove the `All` role. Assign permissions only to authenticated roles like `System Manager` or `Tender Manager`.

### 7. Invalid `party_type` Crashing Journal Entry Workflow
- **File:** `tender_management/tender_management/doctype/bid_security_request/bid_security_request.py` (Line 42)
- **Description:** `party_type` is hardcoded to `"Data"`, which triggers a `DoesNotExistError` on submission and prevents users from submitting the document.
- **Remediation:** Set `party_type` to a valid DocType link (e.g., `Customer` or `Supplier`).

### 8. Dangerous Subprocess Execution (`shell=True` & `pkill -9`)
- **File:** `tender_management/utils/scraper_utils.py` (Lines 175, 226, 227)
- **Description:** Executes system commands using `shell=True` and `pkill -9`, which introduces severe Command Injection vulnerabilities and prevents graceful cleanup, leading to corrupted caches and DB locks.
- **Remediation:** Refactor to use `shell=False` and pass arguments as a list. Use proper process management instead of string-matched `pkill`.

### 9. Massive Collection of Scratch Scripts
- **Directory:** `/home/frappe/frappe-bench/apps/tender_management/deprecated_archive/*`
- **Description:** 152 abandoned scratch scripts executing direct database manipulation reside in this directory, posing significant maintenance and security risks.
- **Remediation:** Delete the deprecated scripts permanently from the active repository.

### 10. N+1 Query in Document Deletion & Compilation
- **File:** `tender_management/utils/tender_doc_gen.py` (Lines 89-98, 232-249)
- **Description:** The code executes single `get_value` and `delete` queries inside a loop over old entries and child table rows, leading to excessive sequential database querying.
- **Remediation:** Extract all relevant identifiers/URLs and utilize a single `frappe.get_all` query with an `in` filter. Perform batched deletions.

---

## 🟠 High Risk

### 1. Server-Side Template Injection (SSTI)
- **File:** `tender_management/utils/tender_doc_gen.py` (Line 205)
- **Description:** `frappe.render_template()` renders content directly from the `Document Template` doctype. Users with edit privileges can inject malicious Jinja2 payloads executing arbitrary code.
- **Remediation:** Restrict access to creating/editing Document Templates, and validate/sanitize input passed to `render_template`.

### 2. IDOR on Document Templates & Row-Level Permission Bypass
- **Files:** `tender_doc_gen.py` (Lines 12-18), `tender_calendar.py` (Lines 35-40)
- **Description:** Fetches Document Templates without checking User Permissions, and uses `frappe.get_all()` instead of `frappe.get_list()` for calendar events, bypassing role-based row-level security.
- **Remediation:** Enforce read permission checks using `has_permission` or utilize `frappe.get_list()` for API data retrieval.

### 3. Privilege Escalation via `ignore_permissions=True`
- **Files:** `tender_doc_gen.py` (Lines 287, 296), `tender_opportunity.py` (Lines 70, 101, 121), `scraper_utils.py` (Line 145)
- **Description:** Multiple APIs allow users with basic `read` access to update documents and create tasks because `insert(ignore_permissions=True)` or `save(ignore_permissions=True)` are used.
- **Remediation:** Remove `ignore_permissions=True` when updating a document on behalf of a user. Enforce correct role requirements.

### 4. Thread-Blocking Subprocess Calls (LibreOffice)
- **File:** `tender_management/utils/docx_converter.py` (Lines 35-40)
- **Description:** Running synchronous `unoconv` blocks Gunicorn web workers, rapidly exhausting them under load.
- **Remediation:** Migrate PDF conversion to a background task or use an actively maintained asynchronous service like `unoserver`.

### 5. Check-Then-Act Race Conditions
- **File:** `tender_management/tender_management/doctype/tender_opportunity/tender_opportunity.py` (Lines 61, 110)
- **Description:** Concurrent requests checking `if not frappe.db.exists(...)` before inserting will duplicate tasks/followers.
- **Remediation:** Utilize unique database constraints or DB-level row locks (`FOR UPDATE`).

### 6. Database Field Overwritten by ORM
- **File:** `tender_management/tender_management/doctype/tender_opportunity/tender_opportunity.py` (Line 102)
- **Description:** Calling `self.db_set` inside `validate()` results in the field reverting to `None` upon the subsequent `save()`.
- **Remediation:** Mutate `self.bid_security_request` directly within `validate()`.

### 7. Vulnerable Dependencies (Frappe 15.0.0 & ESLint)
- **Files:** `pyproject.toml`, `.pre-commit-config.yaml`
- **Description:** The current Frappe version (15.0.0) is vulnerable to authenticated SQL injection (CVE-2026-29081) and Path Traversal. ESLint 8.x is EOL and contains vulnerabilities.
- **Remediation:** Upgrade Frappe to 15.105.0+ and ESLint to v9.x.

### 8. Core Framework Monkey-Patching (File.validate)
- **File:** `tender_management/hooks.py` (Lines 28-45)
- **Description:** Overriding `File.validate` via monkey-patching bypasses extensibility standards and masks the root cause of long filename issues.
- **Remediation:** Utilize `doc_events` hooks or fix the root issue causing overly long filenames.

### 9. High Cyclomatic Complexity & Monolithic Functions
- **File:** `tender_management/utils/tender_doc_gen.py` (Lines 79-299)
- **Description:** `generate_compiled_tender_document_v5` is a massive monolithic function with deep nesting and broad exception handling.
- **Remediation:** Refactor into smaller, testable, and reusable helper functions.

---

## 🟡 Medium Risk

### 1. Regex Replacement Injection / DoS & Re-invented Templating
- **File:** `tender_management/utils/tender_doc_gen.py` (Lines 30-32)
- **Description:** Using `re.sub` for string templating is vulnerable to ReDoS and syntax crashing if user input contains backreferences.
- **Remediation:** Replace regex string templating with Frappe's standard Jinja rendering (`frappe.render_template`).

### 2. Synchronous Dispatching within DB Transactions
- **File:** `tender_management/utils/notification_dispatcher.py` (Lines 42-77)
- **Description:** Synchronous iteration over all team members/followers extending transaction locks and causing N+1 querying.
- **Remediation:** Dispatch emails asynchronously and pre-fetch user info using a single database query.

### 3. Missing Deduplication on Scheduled Scrapers
- **Files:** `tender_management/hooks.py` (Line 200), `scraper_utils.py` (Lines 44-50)
- **Description:** Hourly scheduled background scrapers run blindly. Overlapping executions lead to duplicates and excessive CPU usage.
- **Remediation:** Implement locking or check process state before launching a new scraper instance.

### 4. Blocking Synchronous External API Calls
- **File:** `tender_management/utils/scraper_utils.py` (Line 102)
- **Description:** A whitelisted API executes `requests.get()` synchronously, blocking the web worker.
- **Remediation:** Enqueue external HTTP requests via `frappe.enqueue`.

### 5. Circumventing Standard Lifecycle with `db_set` in `on_submit`
- **File:** `tender_management/tender_management/doctype/bid_security_request/bid_security_request.py` (Line 59)
- **Description:** Bypassing Frappe's synchronization flow by executing `db_set` post-submission.
- **Remediation:** Set the required field in `before_submit`.

### 6. Structural Code Duplication
- **File:** `tender_management/scrapers/merkato_spider.py` (Lines 197-208, 229-237, 240-252, 261-262)
- **Description:** Highly repetitive dictionary fallback checking logic.
- **Remediation:** Abstract into a generic `get_best_value` helper function.

### 7. Broad Exception Handling
- **Files:** `scraper_utils.py`, `notification_dispatcher.py`, `tender_doc_gen.py`
- **Description:** Catching generic `Exception` objects obscures actual system failures and masks programming errors.
- **Remediation:** Catch targeted specific exceptions (e.g., `requests.exceptions.RequestException`, `frappe.exceptions.ValidationError`).

### 8. Hardcoded Absolute Paths
- **File:** `tender_management/utils/scraper_utils.py` (Lines 25, 36, 113, 181)
- **Description:** Hardcodes specific global environment paths (e.g., `/usr/local/bin/bench`), breaking portability.
- **Remediation:** Utilize `frappe.get_app_path()` and dynamic path structures.

### 9. Vulnerable Dependencies (Scrapy & Unoconv)
- **Files:** `pyproject.toml`, `install_dependencies.sh`
- **Description:** Scrapy 2.11.2 has a DoS vulnerability. `unoconv` is archived, unmaintained, and historically susceptible to SSRF/LFI.
- **Remediation:** Upgrade Scrapy to > 2.13.2. Migrate from `unoconv` to `unoserver`.

### 10. Inefficient Raw SQL Query
- **File:** `tender_management/report/strategic_tender_analytics/strategic_tender_analytics.py` (Lines 38-49)
- **Description:** A raw SQL query ignores `docstatus < 2`, incorrectly aggregating cancelled/deleted documents into the analytics.
- **Remediation:** Update the `WHERE` clause to filter out `docstatus = 2`.

---

## 🟢 Low Risk / Informational

### 1. Leftover Deprecated Files with Hardcoded API Keys
- **Directory:** `deprecated_archive/`
- **Description:** Multiple legacy scripts contain hardcoded SMS API keys (`VZRZD8VLZW...`, `3IFW2DBF...`).
- **Remediation:** Revoke the keys and delete the archive folder.

### 2. Extraneous Files & Mock Data
- **Files:** `sample.html`, `tenderdesc.html`, PNG screenshots in root.
- **Description:** Root directory is littered with scratch files containing mock tokens (e.g., reCAPTCHA keys).
- **Remediation:** Remove files or relocate them to `.gitignore`d folders.

### 3. Missing Subprocess Timeouts
- **File:** `tender_management/utils/scraper_utils.py` (Lines 175, 189)
- **Description:** `subprocess.run` calls lack timeouts, creating a risk of indefinite hanging.
- **Remediation:** Always supply a `timeout` parameter to `subprocess.run()`.

### 4. Raw `print()` Statements
- **Files:** `setup.py`, `merkato_spider.py`
- **Description:** Utilizing `print()` instead of `frappe.logger()`, resulting in lost telemetry.
- **Remediation:** Convert `print` statements to standardized logging calls.

### 5. Indexing Gaps
- **Files:** `scraped_tender.json`, `tender_opportunity.json`
- **Description:** Frequently queried date and status fields lack database indexes (`"search_index": 1`).
- **Remediation:** Enable searching and indexing for fields like `status`, `closing_date`, and `publication_date`.

### 6. Unsafe Injection in PDF Messages
- **File:** `tender_management/utils/tender_doc_gen.py` (Line 246)
- **Description:** Filenames are directly concatenated into HTML strings, presenting minor injection risks.
- **Remediation:** Pass variables safely or escape them using `frappe.utils.escape_html`.

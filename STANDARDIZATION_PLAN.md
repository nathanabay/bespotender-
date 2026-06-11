# Tender Management — Standardization Plan

> **Scope:** Installation integrity, path portability, architecture cleanup, and bench supervisor compatibility.
> **Status:** Audit complete — no code has been changed. All items are action items only.
> **Frappe Target:** v15 / ERPNext v15

---

## Executive Summary

| Priority | Count | Description |
|----------|-------|-------------|
| 🔴 CRITICAL | 6 | Will crash bench, corrupt data, or cause silent failures |
| 🟠 HIGH | 7 | Breaks portability, cross-environment installations, or security |
| 🟡 MEDIUM | 8 | Non-standard structure, missing declarations, or maintainability debt |
| 🟢 LOW | 4 | Code quality / cleanup |

---

## Part 1 — Installation Integrity

### 🔴 CRITICAL-1: `frappe.print()` is not a valid Frappe API

**File:** `tender_management/tender_management/setup.py` lines 6-10

`frappe.print()` does not exist. Calling it during `after_install` will throw `AttributeError` and abort the migration, leaving the site in a broken partial-install state.

**Fix:** Replace all five `frappe.print(...)` calls with Python's built-in `print(...)`:

```diff
- frappe.print("--- Tender Management Post-Install ---")
+ print("--- Tender Management Post-Install ---")
```

---

### 🔴 CRITICAL-2: `import frappe` at module level inside `hooks.py`

**File:** `tender_management/hooks.py` line 8

`hooks.py` is parsed by bench **before** the Frappe environment (and database) is initialized. A top-level `import frappe` will silently fail or, worse, trigger partial initialization that corrupts subsequent app loading. This is a known cause of `bench start` supervisor crashes.

**Fix:** Remove line 8 (`import frappe`) entirely. `hooks.py` must be a pure-Python data file with no side-effectful imports.

```diff
  app_license = "mit"
-
- import frappe
-
  # Apps
```

---

### 🔴 CRITICAL-3: Hardcoded company-specific account names in Server Scripts

**File:** `tender_management/tender_management/setup.py` lines 511-592

The `setup_bid_security_accounting()` and `setup_document_purchase_payment()` functions embed verbatim account names tied to a specific installation:

```
"Earnest Money - BES"
"7868687686867 - cbe - BES"
```

These are **hardcoded inside a Server Script string that is dynamically written to the database**. On any site where the company abbreviation is not `BES` or the bank account number differs, the Journal Entry automation will silently post to non-existent accounts, causing crashes or corrupted accounting.

**Fix (two-part):**

1. Replace the literal account names in the script template with dynamic ERPNext lookups inside the script body:
```python
# Replace hardcoded strings with:
earnest_money_account = frappe.db.get_value(
    "Account", {"account_name": "Earnest Money", "company": company}, "name"
)
bank_account = frappe.db.get_value(
    "Account", {"account_type": "Bank", "is_group": 0, "company": company, "disabled": 0}, "name"
)
```

2. Add a guard at the top of each journal block:
```python
if not earnest_money_account or not bank_account:
    frappe.log_error("Required accounts not found.", "CPO JE Automation")
else:
    # ... proceed with JE creation
```

---

### 🔴 CRITICAL-4: `scrapy` is listed as a hard dependency in `pyproject.toml`

**File:** `pyproject.toml` line 12

```toml
dependencies = [
    "scrapy>=2.13.2"
]
```

Scrapy is a heavyweight web-scraping framework (~30 MB, Twisted reactor, OpenSSL). Listing it as a non-optional dependency means **every `bench get-app` or `pip install` of this app will pull Scrapy**, even on sites that never use the scraper.

Furthermore, Scrapy runs its own Twisted event loop (`process.start()`) inside `start_crawling_direct()`. Calling this from inside a Frappe worker (RQ/Gunicorn) **blocks the entire process** until crawling is complete.

**Fix (two-part):**

1. Move `scrapy` to an optional extras group in `pyproject.toml`:
```toml
[project.optional-dependencies]
scraper = ["scrapy>=2.11.0,<3.0"]
```
Install via: `pip install tender_management[scraper]`

2. Guard the import at runtime:
```python
# In start_crawling_direct():
try:
    from scrapy.crawler import CrawlerProcess
except ImportError:
    frappe.throw("Scrapy is not installed. Run: pip install 'tender_management[scraper]'")
```

---

### 🔴 CRITICAL-5: Structural duplication — `doctype/` stub at the wrong module level

**Path:** `tender_management/doctype/`

There is a `doctype/` directory directly inside `tender_management/` (the app root package) that contains only a `__pycache__/` folder. The real doctypes live under `tender_management/tender_management/doctype/`.

Frappe's discovery mechanism scans the **module directory** (the inner `tender_management/tender_management/`) for doctypes. The outer stub adds confusion and `__pycache__` pollution.

**Fix:** Delete the empty directory after confirming no source files exist:
```bash
rm -rf tender_management/doctype/
```

---

### 🔴 CRITICAL-6: `setup.py` is a 916-line monolith — violates Frappe's single-responsibility pattern

**File:** `tender_management/tender_management/setup.py`

At 916 lines, this file mixes: module setup, account creation, dashboard chart creation, number card creation, workspace setup, workflow management, Server Script injection, and document template seeding.

This monolith is the primary source of the hardcoded `BES` account names (CRITICAL-3), makes rollback logic impossible, and makes individual feature additions brittle.

**Fix:** Decompose into a `setup/` package:

```
tender_management/tender_management/
└── setup/
    ├── __init__.py          # exposes after_install() and after_migrate()
    ├── accounts.py          # setup_accounts(), setup_bid_bond_account()
    ├── charts.py            # setup_dashboard_charts(), upsert_dashboard_chart()
    ├── workspace.py         # setup_workspace()
    ├── workflow.py          # setup_enhanced_workflow()
    ├── scripts.py           # setup_bid_security_accounting(), setup_document_purchase_payment()
    └── templates.py         # create_default_document_templates()
```

Update `hooks.py` references:
```python
after_install = "tender_management.tender_management.setup.after_install"
after_migrate  = "tender_management.tender_management.setup.after_migrate"
```

---

## Part 2 — High Priority Issues

### 🟠 HIGH-1: All Python dependencies are unpinned

**File:** `pyproject.toml` lines 10-13

Only `scrapy>=2.13.2` is declared. The following packages are **actively imported** but have no declaration at all:

| Package | Imported In | Risk |
|---------|-------------|------|
| `beautifulsoup4` (`bs4`) | `scraper_utils.py:7` | No version constraint |
| `pypdf` | `docx_converter.py:2`, `tender_doc_gen.py:8` | Breaking API changes between v2 and v3 |
| `requests` | `scraper_utils.py:121` | No version constraint |

**Fix:** Add pinned declarations to `pyproject.toml`:

```toml
dependencies = [
    "beautifulsoup4>=4.12.0,<5.0",
    "pypdf>=4.0.0,<5.0",
    "requests>=2.31.0,<3.0",
    "lxml>=5.0.0",
]
```

---

### 🟠 HIGH-2: `install_dependencies.sh` is a manual, undiscoverable step with no auto-invoke

**File:** `tender_management/install_dependencies.sh`

The script installs `unoconv` (required for DOCX to PDF conversion) but it is never called automatically. On a fresh site, DOCX uploads will silently fail until the admin notices and runs this script manually.

**Fix:** In `setup.py::after_install()`, replace the print message with a proper Frappe-style warning visible in the Desk:

```python
frappe.msgprint(
    msg="This app requires 'unoconv' for DOCX conversion. "
        "Run: <code>sudo apt-get install -y unoconv</code> on the server.",
    title="System Dependency Required",
    indicator="orange"
)
```

---

### 🟠 HIGH-3: `frappe.OutgoingEmailError` does not exist in Frappe v15

**File:** `tender_management/utils/notification_dispatcher.py` line 86

```python
except (frappe.ValidationError, frappe.OutgoingEmailError) as e:
```

`frappe.OutgoingEmailError` is not a real exception class in Frappe v15. This will cause a `NameError` or silently swallow exceptions the first time a sendmail failure occurs.

**Fix:**
```diff
- except (frappe.ValidationError, frappe.OutgoingEmailError) as e:
+ except (frappe.ValidationError, Exception) as e:
```

---

### 🟠 HIGH-4: Fallback file path navigates above app root with `..`

**File:** `tender_management/utils/scraper_utils.py` line 141

```python
local_file = os.path.join(frappe.get_app_path("tender_management"), "..", "tenderdesc.html")
```

This resolves to a file sitting loose at the Git repository root, outside any Python package. It will not be copied on deployment, and the `..` traversal is a code smell.

**Fix:**
1. Move `tenderdesc.html` into `tender_management/tender_management/data/`.
2. Replace the path construction:
```python
local_file = os.path.join(
    frappe.get_app_path("tender_management"), "data", "tenderdesc.html"
)
```

---

### 🟠 HIGH-5: `scrapers/` module is not in a standard Frappe module directory

**Path:** `tender_management/scrapers/`

`scrapers/` sits directly inside the app's Python package root. Additionally, `MerkatoSpider` calls `frappe.get_single()` and `frappe.get_all()` **inside `__init__`**. This executes database queries at spider construction time. When Scrapy is invoked via a detached subprocess (where no Frappe DB connection is active), this will throw `frappe.exceptions.DatabaseError`.

**Fix:**
1. Move `scrapers/` into the module directory: `tender_management/tender_management/scrapers/`
2. Refactor `MerkatoSpider.__init__()` to accept settings as constructor arguments rather than fetching from the database:
```python
# In start_crawling_direct():
settings_doc = frappe.get_single("Tender Scraper Settings")
process.crawl(MerkatoSpider,
    page_limit=int(pages),
    username=settings_doc.merkato_username,
    password=settings_doc.get_password("merkato_password"),
    enabled_categories=[c.category_name for c in settings_doc.categories if c.enabled]
)
```

---

### 🟠 HIGH-6: `SAMPLE_TEMPLATES.md` is a loose non-Python file inside the app package

**File:** `tender_management/SAMPLE_TEMPLATES.md`

A Markdown file sitting inside the Python package directory is invisible to users, served nowhere, and pollutes the import namespace.

**Fix:**
```bash
mkdir -p docs
mv tender_management/SAMPLE_TEMPLATES.md docs/SAMPLE_TEMPLATES.md
```

---

### 🟠 HIGH-7: `company_name` fallback `or "BES"` in `tender_doc_gen.py`

**File:** `tender_management/utils/tender_doc_gen.py` line 30

```python
"company_name": frappe.defaults.get_defaults().get("company") or "BES"
```

Same pattern as the `setup.py` hardcoded `BES` fallback. On any non-BES site, document templates will render the wrong company name silently.

**Fix:** Remove the fallback. If no company default is set, render a placeholder or raise a user-facing error:
```python
"company_name": frappe.defaults.get_defaults().get("company") or frappe.db.get_value("Company", {}, "name") or ""
```

---

## Part 3 — Medium Priority Issues

### 🟡 MEDIUM-1: `or "BES"` fallback in `setup.py` account setup functions

**File:** `tender_management/tender_management/setup.py` — multiple locations

The pattern `frappe.db.get_value("Company", {}, "name") or "BES"` appears in `setup_accounts()`, `setup_bid_bond_account()`, `setup_bid_security_accounting()`, `setup_document_purchase_payment()` and the embedded Server Script strings.

**Fix:** Remove all `or "BES"` fallbacks. Add an early guard:
```python
company = frappe.db.get_value("Company", {}, "name")
if not company:
    frappe.log_error("No company found. Skipping account setup.", "Tender Install")
    return
```

---

### 🟡 MEDIUM-2: `tender_management/config/__init__.py` is empty — missing `desktop.py`

**Path:** `tender_management/config/`

Standard Frappe apps have a `desktop.py` here to register the app in the Desk sidebar module list.

**Fix:** Add `tender_management/config/desktop.py`:
```python
from frappe import _

def get_data():
    return [
        {
            "module_name": "Tender Management",
            "color": "grey",
            "icon": "octicon octicon-file-directory",
            "type": "module",
            "label": _("Tender Management")
        }
    ]
```

---

### 🟡 MEDIUM-3: `notification_dispatcher.py` uses `doc.flags.is_new_doc` — unreliable flag

**File:** `tender_management/utils/notification_dispatcher.py` line 105

`doc.flags.is_new_doc` is set during `before_insert`/`after_insert` lifecycle, not during `on_update`. By the time `on_update` fires, this flag may be `False` even on the first save.

**Fix:** Use a DB existence check instead:
```python
if not frappe.db.exists("Tender Opportunity", doc.name):
    # This is a new document
```

Or move the "new doc" notification to the `after_insert` doc event hook.

---

### 🟡 MEDIUM-4: Scheduler `run_scraper_job` calls `frappe.has_permission()` without guaranteed user context

**File:** `tender_management/utils/scraper_utils.py` lines 26-27 + `hooks.py` line 166

`run_scraper_job` is registered under `scheduler_events.hourly`. Frappe's scheduled task runner does not always set `frappe.session.user` to a meaningful value. Calling `frappe.has_permission()` in this context can fail silently.

**Fix:** Split into two functions:
- `run_scraper_job()` — scheduled version, no permission check, guarded by scheduler context
- `trigger_scraper_job(pages=None)` — `@frappe.whitelist()` decorated, with permission check, called from UI

---

### 🟡 MEDIUM-5: `scrapers/merkato_spider.py` uses `print()` instead of Scrapy logger

**File:** `tender_management/scrapers/merkato_spider.py` lines 34-48

Multiple `print(...)` statements emit to stdout which is swallowed by the detached subprocess.

**Fix:** Replace with Scrapy's built-in logger:
```python
self.logger.info(f"MerkatoSpider initialized — Page Limit: {self.page_limit}")
```

---

### 🟡 MEDIUM-6: `tests/` directory missing `__init__.py`

**Path:** `tender_management/tests/`

Without `__init__.py`, `bench run-tests --app tender_management` may not discover `test_document_generation.py`.

**Fix:**
```bash
touch tender_management/tests/__init__.py
```

---

### 🟡 MEDIUM-7: Subprocess pattern incompatible with containerized bench deployments

**File:** `tender_management/utils/scraper_utils.py` lines 62-68

The `subprocess.Popen` with `start_new_session=True` will have child processes killed by container orchestrators. `pgrep` will fail across PID namespaces. The `open(log_path, "a")` call leaks a file descriptor on failure.

**Recommended fix:** Use Frappe's native queue for long jobs:
```python
frappe.enqueue(
    "tender_management.utils.scraper_utils.start_crawling_direct",
    queue="long",
    timeout=7200,
    pages=int(pages)
)
```

If Scrapy's Twisted reactor conflicts with RQ threading, launch it from within the worker via `subprocess.run()` pointing to a dedicated `scrapers/runner.py` entry point.

---

### 🟡 MEDIUM-8: Empty `patches.txt` — one-time cleanup runs on every migrate

**File:** `tender_management/patches.txt`

Functions like `setup_bid_security_sync()` and `cleanup_legacy_customizations()` are one-time operations but run on every `bench migrate`. They should be patches.

**Fix:**
```
[post_model_sync]
tender_management.patches.v1_0.disable_legacy_bid_security_script
tender_management.patches.v1_0.cleanup_legacy_customizations
```

---

## Part 4 — Low Priority Issues

### 🟢 LOW-1: `hooks.py` references `truncate_file_name` which does not exist in `docx_converter.py`

**File:** `tender_management/hooks.py` lines 151-153

```python
"File": {
    "validate": "tender_management.utils.docx_converter.truncate_file_name"
}
```

`docx_converter.py` only defines `append_document()`. This hook throws `AttributeError` for **every file upload** in the system.

**Fix:** Either add `truncate_file_name()` to `docx_converter.py`, or remove this `doc_events["File"]` entry if unused.

---

### 🟢 LOW-2: Test assertion is locale-dependent

**File:** `tender_management/tests/test_document_generation.py` line 55

```python
self.assertIn("50,000", generated_content)
```

On sites with non-standard money formatting (e.g., `ETB 50,000.00`), this test fails without a code change.

**Fix:**
```python
self.assertRegex(generated_content, r"50[,.]000")
```

---

### 🟢 LOW-3: `@frappe.whitelist()` has no effect on Document class instance methods

**File:** `tender_management/tender_management/doctype/tender_opportunity/tender_opportunity.py` line 46

```python
@frappe.whitelist()
def create_standard_tasks(self):
```

`@frappe.whitelist()` is for module-level functions only. On a Document method, the decorator is silently ignored.

**Fix:** Remove the decorator. If RPC access is needed, add a module-level wrapper:
```python
@frappe.whitelist()
def create_standard_tasks_for(tender_name):
    doc = frappe.get_doc("Tender Opportunity", tender_name)
    doc.check_permission("write")
    doc.create_standard_tasks()
```

---

### 🟢 LOW-4: `_get_log_path()` is the correct pattern — document it as the app standard

**File:** `tender_management/utils/scraper_utils.py` lines 14-17

```python
def _get_log_path():
    site_path = frappe.get_site_path()
    return os.path.join(site_path, "logs", "tender_scraper.log")
```

This is correct. No change needed. ✅ Add a docstring and reference this pattern in any developer documentation so future contributors do not introduce hardcoded `/tmp` or absolute paths.

---

## Remediation Order

Execute fixes in this order to avoid cascading failures:

```
Phase 1 — Stop the bleeding (do before next deployment)
  ├── CRITICAL-1:  Fix frappe.print() → print()
  ├── CRITICAL-2:  Remove 'import frappe' from hooks.py
  └── LOW-1:       Add truncate_file_name() or remove the broken hook (crashes all file uploads)

Phase 2 — Portability (do before deploying to a second site)
  ├── CRITICAL-3:  Parameterize hardcoded account names in Server Scripts
  ├── CRITICAL-4:  Move scrapy to optional dependency
  ├── HIGH-1:      Pin all undeclared Python dependencies
  ├── HIGH-4:      Fix .. path traversal in _sync_categories_background()
  └── HIGH-7:      Fix 'or BES' fallback in tender_doc_gen.py

Phase 3 — Architecture cleanup (do on next sprint)
  ├── CRITICAL-5:  Delete empty tender_management/doctype/ stub directory
  ├── CRITICAL-6:  Decompose setup.py monolith into setup/ package
  ├── HIGH-2:      Surface unoconv missing warning in Desk
  ├── HIGH-3:      Fix frappe.OutgoingEmailError
  ├── HIGH-5:      Move scrapers/ into module directory; decouple DB from __init__
  ├── HIGH-6:      Move SAMPLE_TEMPLATES.md to docs/
  ├── MEDIUM-1:    Remove all 'or BES' fallbacks in setup.py
  └── MEDIUM-2:    Add config/desktop.py

Phase 4 — Quality hardening
  ├── MEDIUM-3:    Fix is_new_doc flag usage
  ├── MEDIUM-4:    Split scheduler vs. UI-facing scraper function
  ├── MEDIUM-5:    Replace print() with self.logger.info() in spider
  ├── MEDIUM-6:    Add tests/__init__.py
  ├── MEDIUM-7:    Migrate to frappe.enqueue for scraper
  ├── MEDIUM-8:    Add one-time patches to patches.txt
  ├── LOW-2:       Fix locale-dependent test assertion
  ├── LOW-3:       Remove @whitelist from instance method
  └── LOW-4:       Add docstring to _get_log_path()
```

---

## Appendix — Files to Audit in Next Pass

| File | Concern |
|------|---------|
| `tender_management/tender_management/page/tender_calendar/tender_calendar.py` | Prior audit noted a hardcoded path at L38 |
| `tender_management/tender_management/doctype/bid_security_request/bid_security_request.json` | Prior audit noted a company-specific default value at L52 |

---

*Generated by deep audit — June 2026. No production files were modified.*

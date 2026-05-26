# System Audit Report: Tender Management System
**Date:** Tuesday, May 26, 2026
**Scope:** Full-stack (Backend, Frontend, Schema, Workflows, Integrations)
**Audit Method:** 10-Agent Distributed Concurrent Analysis

## 🔴 CRITICAL - Immediate Action Required

### 1. Security & Credential Exposure
- **Issue:** Hardcoded API keys found in production code.
- **Locations:**
  - `tender_management/utils/notifications.py`: `CW_TOKEN` (Chatwoot).
  - `tender_management/utils/sms.py`: `api_key` (SMSEthiopia).
  - `archive/`: Multiple scripts contain hardcoded credentials.
- **Risk:** Unauthorized access to external notification systems and potential cost implications.
- **Remediation:** Move all secrets to encrypted fields in a "Tender Settings" DocType or `site_config.json`.

### 2. High-Risk Technical Debt
- **Issue:** "Nuclear" cleanup scripts present in production-facing directories.
- **Locations:** `tender_management/archive/` (e.g., `scorched_earth_fix.py`, `nuclear_dashboard_fix_v2.py`).
- **Risk:** These scripts contain `DELETE FROM tabTender Opportunity` without filters. Accidental execution will cause irreversible data loss.
- **Remediation:** Delete the `archive/` folder. All historical scripts are preserved in Git history.

### 3. Broken Access Control
- **Issue:** `@frappe.whitelist()` methods lack explicit permission checks.
- **Locations:** `send_sms`, `notify_chatwoot`, `get_calendar_events`, and `download_pdf`.
- **Risk:** Any logged-in user (regardless of role) could potentially trigger SMS/notifications or view sensitive calendar data.
- **Remediation:** Implement `frappe.has_permission()` checks in all whitelisted backend methods.

---

## 🟠 HIGH - Stability & Integrity Risks

### 4. Database Schema Mismatches
- **Issue:** Logical discrepancies in `Bid Security Request`.
- **Details:** Scripts reference `tender_opportunity.organization`, but the field in the DocType is named `tender`.
- **Risk:** Errors when fetching data for Bid Bonds or during automated generation of requests.
- **Remediation:** Standardize naming to `tender_opportunity` across all related DocTypes.

### 5. Workflow Deadlocks & Bypasses
- **Issue:** Conflicting workflow definitions (JSON vs `setup.py`) and missing `allow_on_submit` flags.
- **Risk:** 
  - Users are locked out of updating `final_contract_value` once a tender is "Won".
  - `allow_self_approval` is enabled, compromising the 4-eyes principle.
- **Remediation:** 
  - Set `allow_on_submit: 1` for outcome fields.
  - Consolidate workflow logic into a single declarative JSON/Workflow DocType.
  - Disable `allow_self_approval` for critical stages.

### 6. Fragile Accounting Logic
- **Issue:** Hardcoded string matching for "Bid Bond" account names.
- **Risk:** Automation fails if the Chart of Accounts is modified or localized.
- **Remediation:** Use a configuration field in "Tender Settings" to select the appropriate ledger account by name or code.

---

## 🟡 MEDIUM - Performance & UX Improvements

### 7. Performance Bottlenecks
- **Issue:** Synchronous external API calls in loops (Chatwoot reminders).
- **Risk:** Scheduled jobs will timeout or crash as the number of tenders grows.
- **Remediation:** Move external notification calls to `frappe.enqueue` for background processing.

### 8. Dashboard & UI Inconsistencies
- **Issue:** `Tender Pipeline Value` uses `Count` instead of `Sum`.
- **Issue:** Workspace links to non-existent components (`Tasks by Status`).
- **Issue:** `Tender Board` page implementation files are missing.
- **Remediation:** 
  - Update Dashboard Chart to use `Sum(final_bid_price)`.
  - Remove dead workspace links.
  - Restore or remove the `Tender Board` ghost page.

### 9. Database Optimization
- **Issue:** Missing indexes on high-traffic filter fields.
- **Locations:** `sector`, `submission_deadline`, `status`.
- **Remediation:** Add `search_index: 1` to these fields in the DocType JSON definitions.

---

## ✅ COMPLIANCE SUMMARY
- **Spec Alignment:** Generally high (>90%) with `BESPO_TENDER_FORMS_COMPLETE.md`.
- **Gaps:** "Manage Milestones" is a UI placeholder; SMS and Chatwoot integrations are undocumented in the feature list.

**Report Prepared By:** Gemini CLI Agent Team
**Status:** Audit Finalized - Awaiting Remediation Plan Approval.

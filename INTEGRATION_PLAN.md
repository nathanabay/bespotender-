# Integration Recommendation Plan: Tender Management & Bespo Notifications
**Date:** Tuesday, May 26, 2026
**Version:** 1.4 (Unified Configuration & Global Routing)

## 1. Executive Summary
The goal is to migrate the legacy, synchronous notification system in `tender_management` (Chatwoot/SMS) to the robust, multi-channel, and audited framework provided by `bespo_notifications`. 

**Update (v1.4):** This version formalizes the **Unified Configuration** strategy. To prevent redundancy and credential drift, the Telegram Bot Token will be fetched exclusively from **Bespo Notification Settings**.

---

## 2. Phase 1: Legacy Decommissioning (Cleanup)
*(Status: Complete)*
- Deleted `tender_management/utils/sms.py`.
- Stripped Chatwoot logic from `notifications.py`.
- Verified removal of `cw_token`, `cw_url`, and `sms_api_key` from site configuration.

---

## 3. Phase 2: Configuration & Settings

### 3.1 Global: Tender Settings DocType
A **Single DocType** named `Tender Settings` manages Tender-specific routing.
- **Fields:**
  - `default_tender_manager` (Link: User): Default assignee for new opportunities.
  - `lost_tender_recipient` (Link: User): Senior stakeholder to be notified of all "Lost" tenders.
  - `cpo_expiry_recipient` (Link: User): Primary contact for financial bond alerts.
  - `enable_tender_notifications` (Check): Master switch for Tender-specific alerts.
- **Note:** `telegram_bot_token` has been removed from this DocType. All Telegram dispatch logic now fetches the token from `Bespo Notification Settings`.

### 3.2 User-Level: Personal Alert Preferences
Custom fields added to the `User` DocType for individual opt-in/opt-out:
- `receive_tender_deadline_alerts` (Check)
- `receive_workflow_state_alerts` (Check)
- `receive_cpo_expiry_alerts` (Check)

---

## 4. Phase 3: Dynamic Routing & "Watch" Logic

### 4.1 The "Watch" Feature
- **Child DocType:** `Tender Follower` (Field: `user` Link: User).
- **Tender Opportunity:** Child table `followers`.
- **UI:** "Watch/Unwatch" button in document header.

### 4.2 Updated Dispatcher Logic
The `notification_dispatcher.py` implements hierarchical routing and respects Bespo's master settings and User-level toggles.

---

## 5. Phase 4: Scheduled Job Consolidation
*(Status: Complete)*
- Migrated `check_tender_deadlines` to `bespo_notifications/tasks.py`.
- Updated Bespo's Daily Digest to include Tender Deadlines.
- Decommissioned redundant scheduler events in `tender_management/hooks.py`.

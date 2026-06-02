# Integration Recommendation Plan: Tender Management & Bespo Notifications
**Date:** Tuesday, May 26, 2026
**Version:** 1.5 (Multi-Bot & Multi-Channel Routing)

## 1. Executive Summary
The goal is to migrate the legacy, synchronous notification system in `tender_management` (Chatwoot/SMS) to the robust, multi-channel, and audited framework provided by `bespo_notifications`. 

**Update (v1.5):** This version incorporates **Multi-Bot and Multi-Channel** management capabilities derived from `bespo_notifications`. Instead of a single static bot, the system will support routing Tender Alerts through specific Telegram Bots and Channel Profiles based on global defaults or per-tender configurations.

---

## 2. Phase 1: Legacy Decommissioning (Cleanup)
*(Status: Complete)*
- Deleted `tender_management/utils/sms.py`.
- Stripped Chatwoot logic from `notifications.py`.
- Verified removal of `cw_token`, `cw_url`, and `sms_api_key` from site configuration.

---

## 3. Phase 2: Multi-Bot Configuration & Settings

### 3.1 Global: Tender Settings DocType
The `Tender Settings` Single DocType manages default notification pathways.
- **Recipient Fields:**
  - `default_tender_manager` (Link: User)
  - `lost_tender_recipient` (Link: User)
  - `cpo_expiry_recipient` (Link: User)
- **Multi-Bot & Channel Fields (NEW):**
  - `default_notification_bot` (Link: Telegram Bot): Selects the default bot (e.g., "Tender Alert Bot") to dispatch system messages.
  - `default_notification_channel` (Link: Telegram Chat Profile): Selects a default group/channel for broadcast alerts.
  - `enable_tender_notifications` (Check): Master switch.

### 3.2 User-Level: Personal Alert Preferences
Custom fields on the `User` DocType:
- `receive_tender_deadline_alerts` (Check)
- `receive_workflow_state_alerts` (Check)
- `receive_cpo_expiry_alerts` (Check)

---

## 4. Phase 3: Dynamic Routing & Per-Tender Overrides

### 4.1 Per-Tender Departmental Routing (NEW)
Different departments (e.g., Construction vs. IT) may require their tenders to be broadcast via different bots or to different chat groups.
- **Action:** Add overrides to the `Tender Opportunity` DocType.
- **Fields:**
  - `notification_bot` (Link: Telegram Bot)
  - `notification_channel` (Link: Telegram Chat Profile)
- **Logic:** If populated, these fields override the global `Tender Settings` defaults for this specific tender.

### 4.2 The "Watch" Feature
- **Child DocType:** `Tender Follower` (Field: `user` Link: User).
- **Tender Opportunity:** Child table `followers`.
- **UI:** "Watch/Unwatch" button in document header.

### 4.3 Multi-Bot Dispatcher Logic
The `notification_dispatcher.py` handles multi-bot selection:
1. Identify target bot: `doc.notification_bot` OR `Tender Settings.default_notification_bot`.
2. Determine channel: Private message to User OR broadcast to `doc.notification_channel`.
3. Dispatch via `Notification Log`, ensuring the `linked_bot` field is set correctly to maintain accurate audit trails per bot.

---

## 5. Phase 4: Scheduled Job Consolidation
*(Status: Complete)*
- Migrated `check_tender_deadlines` to `bespo_notifications/tasks.py`.
- Updated Bespo's Daily Digest to include Tender Deadlines.
- Decommissioned redundant scheduler events in `tender_management/hooks.py`.

---

## 6. Implementation Roadmap for Version 1.5
1. **Schema Update:** Add `Telegram Bot` and `Telegram Chat Profile` Link fields to `Tender Settings`.
2. **Per-Tender Logic:** Add the same Link fields to `Tender Opportunity` for departmental override.
3. **Dispatcher Upgrade:** Refactor `notification_dispatcher.py` to pass the dynamically selected `linked_bot` into the `Notification Log` payload.
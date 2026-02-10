# Tender Management

**Tender Management** is a Frappe application designed to streamline the entire tender process, from identification to outcome analysis. It helps organizations track opportunities, manage deadlines, assess risks, and analyze results to improve win rates.

## Features

### 🎯 Tender Opportunity Lifecycle
Track the complete journey of a tender:
*   **Identification**: Record initial details like sector, client, and critical dates.
*   **Buying the Document**: Manage payment requests and receipts for tender documents.
*   **Bid Security**: Track various types of bonds (CPO, Bank Guarantee), amounts, and expiry dates.
*   **Proposal Development**: Collaborate on technical and financial proposals, costing, and margin analysis.
*   **Submission**: Ensure timely submission with automated deadline reminders.
*   **Outcome**: Record whether the tender was Won, Lost, or Cancelled, including reasons for loss.

### 📊 Decision Matrix (Go / No-Go)
Make data-driven decisions on whether to bid:
*   **Bid Probability Score**: Automatically calculated score based on customizable factors.
*   **Strategic Alignment**: Assess fit with organizational goals.
*   **Resource Availability**: Ensure team capacity.

### 🔔 Smart Notifications
Stay informed with integrated alerts:
*   **Chatwoot Integration**: Get real-time updates on new tenders and workflow changes directly in your support dashboard.
*   **Email Alerts**: Critical status changes (e.g., "Approved to Bid") trigger instant emails to key stakeholders.
*   **Deadline Reminders**: Daily scheduled jobs check for upcoming deadlines (2 days out) to prevent last-minute rushes.

### 🛡 Risk Management
Proactively identify and mitigate risks:
*   **Risk Categorization**: Technical, Commercial, and Financial risk assessments (Low/Medium/High).
*   **Competition Analysis**: Track known competitors and the intensity of competition.

## Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
bench get-app https://github.com/bespo-et/bespotender-
bench install-app tender_management
```

## Configuration

### Notifications Setup

The app uses **Chatwoot** for notifications. Ensure the following constants are configured in `tender_management/utils/notifications.py` or through Site Configuration (recommended for production):

*   `CW_URL`: Your Chatwoot instance URL.
*   `CW_TOKEN`: API Access Token.
*   `CW_ACCOUNT_ID`: Your Chatwoot Account ID.

### Scheduled Jobs

The system automatically schedules:
*   `daily`: Checks for tenders with a submission deadline in 2 days and workflow state not terminal (e.g., Submitted/Won/Lost).

## License

MIT

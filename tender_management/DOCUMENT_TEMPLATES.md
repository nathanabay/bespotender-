# Tender Management - Available Document Templates

This document lists the standard and sample document templates available for automated generation within the Tender Management system.

---

## 📋 Standard Templates (Seeded)
These templates are automatically created during system setup.

### 1. Standard Cover Letter
*   **Category**: Cover Letter
*   **Purpose**: A formal submission letter addressing the client organization.
*   **Key Placeholders**: `{{organization}}`, `{{tender_title}}`, `{{tender_number}}`, `{{final_bid_price}}`.

### 2. Standard Executive Summary
*   **Category**: Executive Summary
*   **Purpose**: A high-level overview of the bid's value proposition and company expertise.
*   **Key Placeholders**: `{{company_name}}`, `{{sector}}`, `{{tender_title}}`.

### 3. Technical Methodology Template
*   **Category**: Methodology
*   **Purpose**: Outlines the technical approach, from initiation to closure.
*   **Key Placeholders**: `{{tender_title}}`, `{{organization}}`.

---

## 🧪 Sample & Extended Templates
Additional templates available for manual import or customization.

### 4. Compliance Checklist
*   **Category**: Compliance Matrix
*   **Purpose**: A tabular view to demonstrate alignment with tender requirements.
*   **Format**: HTML Table with status indicators (Compliant/Non-Compliant).

---

## 🏷️ Supported Categories
When creating custom templates, you can use these categories to organize your library:
*   Cover Letter
*   Technical Proposal
*   Financial Proposal
*   Executive Summary
*   Company Profile
*   Compliance Matrix
*   Methodology
*   Quality Plan
*   Contract Terms

---

## 🧩 Global Placeholder Reference
Use these tags in any template to automatically pull data from the parent `Tender Opportunity`:

| Placeholder | Component | Description |
| :--- | :--- | :--- |
| `{{tender_title}}` | Core | The name of the Tender |
| `{{organization}}` | Client | Client company/organization name |
| `{{tender_number}}` | Core | Internal or external reference number |
| `{{submission_deadline}}`| Dates | Submission date and time |
| `{{final_bid_price}}` | Finance | Your final submitted bid amount |
| `{{sector}}` | Category| Primary sector (e.g., Construction) |
| `{{tender_type}}` | Category| Type (e.g., RFP, RFQ) |
| `{{company_name}}` | Branding| Your company's name |

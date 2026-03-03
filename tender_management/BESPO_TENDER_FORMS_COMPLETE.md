# BespoTender - Complete Forms Specification
## Exhaustive Field-by-Field Documentation

This document provides **complete** technical details for every form and field within the BespoTender Tender Management system.

---

## 📑 Table of Contents
1. [Tender Opportunity (Main Hub)](#tender-opportunity)
2. [Tender Task](#tender-task)
3. [Cost Estimation](#cost-estimation)
4. [Bid Decision Matrix](#bid-decision-matrix)
5. [Performance Bond](#performance-bond)
6. [Bid Security & Bid Security Request](#bid-security)
7. [Competitor (Master)](#competitor)
8. [Document Template](#document-template)
9. [Tender Content Library](#tender-content-library)
10. [Child Table Forms](#child-table-forms)

---

## 1. Tender Opportunity
**DocType**: Tender Opportunity | **Submittable**: Yes | **Naming**: Naming Series | **Module**: Tender Management

### General Properties
- **Permissions**: System Manager (Full), Tender Director (Full except Delete), Tender Manager (Create/Submit/Write), Tender User (Create/Write)
- **Search Fields**: `tender_number`, `title`, `organization`  
- **Title Field**: `title`
- **Tracks Changes**: Yes

### Business Logic & Validations

#### Auto-Creation Features
1. **Standard Tasks**: 7 standard tasks are auto-created after document insertion:
   - Review Tender Requirements (High priority, +2 days)
   - Bid/No-Bid Decision (High priority, +3 days)
   - Prepare Technical Proposal (Medium priority, +7 days)
   - Prepare Financial Proposal (Medium priority, +7 days)
   - Obtain Bid Security (High priority, +5 days)
   - Final Quality Review (Medium priority, +10 days)
   - Submission Confirmation (High priority, +12 days)

2. **Bid Security Request Auto-Creation**: Triggered when `workflow_state` = "Tender Purchased"
   - Only creates if `bond_amount` is set and no existing `bid_security_request` link
   - Auto-sets: `type` (from `bond_type` or "CPO"), `amount` (from `bond_amount`), `validity_period_days` (from `bond_validity_days` or 90)
   - Auto-selects first available bank account

#### Workflow State Validations
| Workflow State | Required Fields | Additional Checks |
|---|---|---|
| **Tender Purchased** | `purchase_date`, `purchase_receipt_no` | Both must be filled |
| **Bid Bond Issued** | `bid_security_request` (Link) | Linked BSR must have status = "Issued" |
| **Ready for Submission** | `technical_proposal`, `financial_proposal_doc` | Both attachments required |

#### Event Handlers
- `validate()`: Runs state validations and auto-creates BSR
- `after_insert()`: Creates 7 standard tasks automatically

---

### Tab: Identify

#### Section: Header Information
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `naming_series` | Series | Select | T-OPP-, T-CON-, T-ELEC-, T-WAT- | ✓ | | Auto-naming |
| 2 | `title` | Tender Title | Data | | ✓ | | Unique, In List View |
| 3 | `organization` | Organization / Client | Data | | ✓ | | |
| 4 | `sector` | Sector | Select | Construction, Electro-Mechanical, Maintenance, Water Works, General Supply | ✓ | | |
| 5 | `tender_type` | Tender Type | Select | RFP, RFQ, RFT, EOI, ITT, PQQ, Unsolicited Proposal | ✓ | | |
| 6 | `workflow_state` | Workflow State | Link | Workflow State | | | Read Only |
| 7 | `status` | Status | Select | Open, Closed | | | |
| 8 | `tender_number` | Tender Number / Ref | Data | | | | External reference |
| 9 | `url` | Tender Link | Data | | | | URL to source |
| 10 | `source_evidence` | Source Evidence | Attach Image | | | | Screenshot/proof |
| 11 | `driver_name` | Assigned Driver | Data | | | | Person who handles docs |

#### Section: ESG & Social Value
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 12 | `esg_impact_score` | ESG Impact Score | Select | Low, Medium, High | | Medium | |
| 13 | `environmental_initiatives` | Environmental Initiatives | Small Text | | | | Carbon reduction, etc. |
| 14 | `social_value_commitment` | Social Value Commitment ($) | Currency | | | | Monetary value |
| 15 | `governance_compliance` | Governance Compliance Checked? | Check | | | 0 | Boolean flag |

#### Section: Critical Dates
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 16 | `publication_date` | Publication Date | Date | | | | When tender was announced |
| 17 | `submission_deadline` | Submission Deadline | Datetime | | ✓ | | In List View, Critical |
| 18 | `clarification_deadline` | Clarification Deadline | Date | | | | Last date for questions |
| 19 | `site_visit_date` | Site Visit | Datetime | | | | Optional site inspection |
| 20 | `pre_bid_meeting_date` | Pre-Bid Meeting | Datetime | | | | Mandatory meeting date |
| 21 | `decision_date` | Decision Date | Date | | | | Expected award date |

#### Section: Document Purchase
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 22 | `document_price` | Purchase Price | Currency | | | | Cost to buy tender docs |
| 23 | `purchase_date` | Purchase Date | Date | | | | When docs were bought |
| 24 | `purchase_receipt_no` | Receipt No | Data | | | | Finance reference |
| 25 | `doc_purchase_status` | Purchase Status | Select | Pending Assignment, Pending Request, Finance Review, Funds Released, Completed | | Pending Assignment | Workflow status |
| 26 | `tender_purchaser` | Tender Purchaser | Link | User | | | Who bought the docs |
| 27 | `doc_purchase_payment_entry` | Payment Entry | Link | Payment Entry | | | Read Only, ERP link |

---

### Tab: Tender Files
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 28 | `full_tender_document` | Full Tender Document (PDF) | Attach | | | | Allow on submit |
| 29 | `technical_proposal` | Technical Proposal | Attach | | | | Your technical response |
| 30 | `financial_proposal_doc` | Financial Proposal (File) | Attach | | | | Your financial response |
| 31 | `payment_receipt_proof` | Purchase Receipt (Scan) | Attach | | | | Proof of payment, allow on submit |
| 32 | `generated_documents` | Generated Documents | Table | Tender Generated Document | | | Auto-generated docs from templates |

---

### Tab: Qualify

#### Section: Go / No-Go Decision
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 33 | `bid_probability_score` | Win Probability | Percent | | | | Likelihood of winning |
| 34 | `incumbent_vendor` | Incumbent Vendor? | Data | | | | Who currently has contract |
| 35 | `decision_approver` | Decision Approver | Link | User | | | Who approves bid/no-bid |
| 36 | `decision_notes` | Decision Notes | Small Text | | | | Rationale for decision |
| 37 | `decision_matrix` | Decision Matrix | Table | Bid Decision Factor | | | Scoring criteria |

#### Section: Strategic Qualification
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 38 | `strategic_alignment_score` | Strategic Alignment | Select | Low, Medium, High | | Medium | Alignment with strategy |
| 39 | `historical_win_rate_with_client` | Client Win Rate (Historical) | Percent | | | | Past success rate |
| 40 | `opportunity_cost_assessment` | Opportunity Cost Assessment | Small Text | | | | What we're giving up |

#### Section: Risk Assessment
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 41 | `technical_risk` | Technical Risk | Select | Low, Medium, High | | | Execution difficulty |
| 42 | `commercial_risk` | Commercial Risk | Select | Low, Medium, High | | | Payment/contract risk |
| 43 | `financial_risk` | Financial Risk | Select | Low, Medium, High | | | Profitability risk |
| 44 | `scope_creep_risk` | Scope Creep Risk | Select | Low, Medium, High | | Low | Undefined scope |
| 45 | `resource_availability_risk` | Resource Availability Risk | Select | Low, Medium, High | | Low | Team capacity |
| 46 | `reputational_risk` | Reputational Risk | Select | Low, Medium, High | | Low | Brand damage risk |
| 47 | `competition_level` | Competition Level | Select | Low, Moderate, Intense, Locked Spec | | | Competitive landscape |
| 48 | `customer_relationship` | Customer Relationship | Select | New Client, Existing - Good, Existing - Strained, Blacklisted | | | Relationship status |

#### Section: Competition
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 49 | `competitors` | Competitors | Table | Tender Competitor | | | List of rival bidders |

#### Section: Budget & Costing
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 50 | `estimated_cost` | Estimated Cost | Currency | | | | Direct cost estimate |
| 51 | `margin_percentage` | Margin % | Percent | | | | Profit margin |
| 52 | `final_bid_price` | Final Bid Price | Currency | | | | Total bid amount |
| 53 | `budget_source` | Budget Source | Data | | | | Funding origin |
| 54 | `project_duration_months` | Duration (Months) | Int | | | | Project length |
| 55 | `payment_terms` | Payment Terms | Data | | | | Payment schedule |

---

### Tab: Plan

#### Section: Kick-off Meeting
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 56 | `kickoff_meeting_notes` | Kick-off Meeting Notes | Text Editor | | | | Meeting summary |

#### Section: Strategic Alignment
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 57 | `win_themes` | Win Themes | Text Editor | | | | Why we will win |
| 58 | `customer_hot_buttons` | Customer Hot Buttons | Small Text | | | | Client priorities |
| 59 | `key_success_factors` | Key Success Factors | Small Text | | | | Critical success criteria |

#### Section: Data & Evidence Strategy
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 60 | `key_data_points` | Key Data Points (Metrics) | Small Text | | | | Stats for proposal |
| 61 | `visualisation_required` | Visualisation Required? | Check | | | 0 | Need charts? |
| 62 | `narrative_strategy` | Narrative Strategy / Storyboard | Text Editor | | | | Story flow |

#### Section: Compliance & Gov Watchpoints
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 63 | `price_lock_in_risk` | Price Lock-in Risk? | Check | | | 0 | Pricing constraints |
| 64 | `supply_chain_volatility_risk` | Supply Chain Volatility Risk | Select | Low, Medium, High | | | Material availability |
| 65 | `contractual_clause_review` | Legal Review Complete? | Check | | | 0 | Legal clearance |
| 66 | `payment_terms_negotiated` | Payment Terms Negotiated? | Check | | | 0 | Terms agreed |
| 67 | `team_capacity_check` | Team Capacity Confirmed? | Check | | | 0 | Resources available |

#### Section: Capture Plan
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 68 | `customer_pain_points` | Customer Pain Points | Text Editor | | | | Client challenges |
| 69 | `solution_overview` | Solution Overview | Text Editor | | | | Our solution |
| 70 | `value_proposition` | Value Proposition | Text Editor | | | | Why choose us |
| 71 | `executive_summary_themes` | Executive Summary Themes | Text Editor | | | | Exec summary content |

---

### Tab: Proposal

#### Section: Bid & Proposal Planner
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 72 | `proposal_sections` | Proposal Sections | Table | Proposal Section | | | Section planner |

#### Section: Submission Compliance Checklist
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 73 | `mandatory_requirements_met` | Mandatory Requirements Met? | Check | | | 0 | All requirements |
| 74 | `compliance_matrix_complete` | Compliance Matrix Complete? | Check | | | 0 | Matrix done |
| 75 | `formatting_check` | Formatting Check? | Check | | | 0 | Font, margins OK |
| 76 | `submission_format_validated` | Submission Format Validated? | Check | | | 0 | Hard/soft copy |
| 77 | `quotation_ref` | Linked Quotation | Link | Quotation | | | ERP quotation link |

#### Section: BOQ / Items
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 78 | `items` | Items | Table | Tender BOQ Item | | | Bill of Quantities |

---

### Tab: Bid Bond

#### Section: Bid Security (CPO)
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 79 | `bond_type` | Bond Type | Select | CPO, Bank Guarantee, Insurance Bond, Performance Bond | | | Security type |
| 80 | `bond_amount` | Bond Amount | Currency | | | | Bond value |
| 81 | `bond_percentage` | Bond Percentage | Percent | | | | % of bid price |
| 82 | `bond_expiry` | Bond Expiry | Date | | | | Validity end date |
| 83 | `bond_validity_days` | Validity (Days) | Int | | | | Duration in days |
| 84 | `bid_security_request` | Bid Security Request | Link | Bid Security Request | | | Link to request form |
| 85 | `bond_status` | Bond Status | Read Only | | | | Fetched from request |
| 86 | `bond_number` | Bond Number | Read Only | | | | Fetched from request |
| 87 | `bank_name` | Bank Name | Data | | | | Read Only |
| 88 | `cpo_journal_entry` | CPO Journal Entry | Read Only | | | | Fetched from request |

---

### Tab: Collaborate

#### Section: Tender Team
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 89 | `team_members` | Team Members | Table | Tender Team Member | | | Assigned team |

#### Section: Discussion & Comments
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 90 | `comments` | Comments | Table | Tender Comment | | | Internal discussions |

---

### Tab: Outcome

#### Section: Negotiation & Clarifications
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 91 | `clarification_questions` | Clarification Questions | Table | Clarification Question | | | Q&A with client |
| 92 | `negotiation_notes` | Negotiation Notes | Text Editor | | | | Negotiation log |
| 93 | `final_contract_value` | Final Contract Value | Currency | | | | Negotiated amount |

#### Section: Post-Bid Presentation
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 94 | `shortlisted_for_presentation` | Shortlisted for Presentation? | Check | | | 0 | Made shortlist? |
| 95 | `presentation_date` | Presentation Date | Datetime | | | | Presentation slot |
| 96 | `presentation_leader` | Presentation Leader | Link | User | | | Who leads |
| 97 | `presentation_feedback` | Presentation Feedback | Small Text | | | | Client comments |

#### Section: Outcome & Debrief
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 98 | `loss_reason` | Loss Reason | Select | Price High, Technical Fail | | | Why we lost |
| 99 | `winning_bid_price` | Winning Bid Price | Currency | | | | Winner's price |
| 100 | `price_difference` | Price Difference | Currency | | | | Gap to winner |
| 101 | `client_feedback_score` | Client Feedback Score (1-10) | Select | 1-10 | | | Client rating |
| 102 | `main_weakness_identified` | Main Weakness Identified | Small Text | | | | Our weakness |
| 103 | `debrief_notes` | Debrief Notes | Text | | | | Debrief summary |
| 104 | `lessons_learned` | Lessons Learned | Text Editor | | | | Future improvements |

#### Section: Reporting Metrics
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 105 | `revenue_potential` | Revenue Potential | Currency | | | | Total value |
| 106 | `weighted_revenue` | Weighted Revenue | Currency | | | | Prob × Value |
| 107 | `forecast_quarter` | Forecast Quarter | Select | Q1, Q2, Q3, Q4 | | | Expected quarter |

---

## 2. Tender Task
**Naming**: `TASK-{tender}-{####}` | **Permissions**: Tender User, Tender Manager (Full)

| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `tender` | Tender Opportunity | Link | Tender Opportunity | ✓ | | Parent tender |
| 2 | `title` | Task Title | Data | | ✓ | | In List View |
| 3 | `description` | Description | Small Text | | | | Details |
| 4 | `assigned_to` | Assigned To | Link | User | ✓ | | Responsible person |
| 5 | `due_date` | Due Date | Date | | ✓ | | Target completion |
| 6 | `status` | Status | Select | Open, In Progress, Completed, Cancelled | | Open | Task state |
| 7 | `priority` | Priority | Select | Low, Medium, High, Urgent | | Medium | Urgency level |
| 8 | `completion_date` | Completion Date | Date | | | | When completed |
| 9 | `completion_notes` | Completion Notes | Small Text | | | | Depends on status=Completed |

---

## 3. Cost Estimation
**Naming**: `CE-{tender}-{####}` | **Permissions**: Tender Manager (Full), Tender User (Create/Read/Write)

### Business Logic & Calculations

#### Auto-Calculated Fields (on Validate)
All calculations run automatically when the document is saved:

1. **Total Direct Cost** = Sum of all `items[].total_cost`
2. **Overhead Amount** = `total_direct_cost` × (`overhead_percentage` / 100)
3. **Subtotal** = `total_direct_cost` + `overhead_amount`
4. **Profit Amount** = `subtotal` × (`profit_margin_percentage` / 100)
5. **Total Price** = `subtotal` + `profit_amount`

#### Event Handlers
- `validate()`: Triggers `calculate_totals()` which computes all read-only currency fields

---

### Fields

| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `tender` | Tender Opportunity | Link | Tender Opportunity | ✓ | | Parent tender |
| 2 | `estimation_date` | Estimation Date | Date | | | Today | When estimated |
| 3 | `status` | Status | Select | Draft, Under Review, Approved, Rejected | | Draft | Approval state |
| 4 | `approved_by` | Approved By | Link | User | | | Who approved |
| 5 | `items` | Items | Table | Cost Item | | | BOQ line items |
| 6 | `total_direct_cost` | Total Direct Cost | Currency | | | | Read Only, sum of items |
| 7 | `overhead_percentage` | Overhead % | Percent | | | 15 | Default 15% |
| 8 | `overhead_amount` | Overhead Amount | Currency | | | | Read Only, calculated |
| 9 | `profit_margin_percentage` | Profit Margin % | Percent | | | 10 | Default 10% |
| 10 | `profit_amount` | Profit Amount | Currency | | | | Read Only, calculated |
| 11 | `total_price` | Total Price | Currency | | | | Read Only, **bold** |
| 12 | `notes` | Notes | Text | | | | Additional notes |

---

## 4. Bid Decision Matrix
**Naming**: `BDM-{tender}-{####}` | **Permissions**: Tender Manager (Full), Tender User (Read/Write)

### Business Logic & Auto-Suggestions

#### Auto-Calculated Fields (on Validate)
1. **Total Score** = Sum of all 7 scoring criteria (each 0-10)
   - `win_probability_score` + `profitability_score` + `strategic_fit_score` + `resource_availability_score` + `technical_capability_score` + `client_relationship_score` + `competition_intensity_score`

2. **Suggested Decision**:
   - If `total_score` ≥ 50 → "Bid"
   - If `total_score` < 50 → "No-Bid"

3. **Decision Date**: Auto-set to today if blank

#### Event Handlers
- `validate()`: Calculates `total_score` and suggests decision

---

### Fields

| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `tender` | Tender Opportunity | Link | Tender Opportunity | ✓ | | Parent tender |
| 2 | `decision_date` | Decision Date | Date | | | Today | When decided |
| 3 | `decision` | Decision | Select | Pending, Bid, No-Bid | ✓ | Pending | Final decision |
| 4 | `approved_by` | Approved By | Link | User | | | Who approved |
| 5 | `win_probability_score` | Win Probability | Int | 0-10 | | | Score 0-10 |
| 6 | `profitability_score` | Profitability | Int | 0-10 | | | Score 0-10 |
| 7 | `strategic_fit_score` | Strategic Fit | Int | 0-10 | | | Score 0-10 |
| 8 | `resource_availability_score` | Resource Availability | Int | 0-10 | | | Score 0-10 |
| 9 | `technical_capability_score` | Technical Capability | Int | 0-10 | | | Score 0-10 |
| 10 | `client_relationship_score` | Client Relationship | Int | 0-10 | | | Score 0-10 |
| 11 | `competition_intensity_score` | Competition Level | Int | 0-10 | | | Higher = less competition |
| 12 | `total_score` | Total Score | Int | | | | Read Only, sum |
| 13 | `suggested_decision` | Suggested Decision | Data | | | | Read Only, automated |
| 14 | `decision_notes` | Decision Notes | Text Editor | | | | Rationale |
| 15 | `no_bid_reason` | No-Bid Reason | Select | Low Win Probability, Insufficient Profit, Resource Constraints, etc. | | | Depends on decision=No-Bid |

---

## 5. Performance Bond
**Naming**: `PB-{tender}-{####}` | **Permissions**: Tender Manager (Full), Tender User (Read)

### Business Logic & Validations

#### Date Validation (on Validate)
- **Expiry Date Check**: `expiry_date` must be >= `issue_date`
  - Error: "Expiry date cannot be before issue date"

---

### Fields

| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `tender` | Tender Opportunity | Link | Tender Opportunity | ✓ | | Parent tender |
| 2 | `bond_number` | Bond Number | Data | | ✓ | | Unique ID |
| 3 | `bond_type` | Bond Type | Select | Performance Bond, Advance Payment Bond, Retention Money Bond, Maintenance Bond | | Performance Bond | Type |
| 4 | `status` | Status | Select | Active, Released, Expired, Claimed | | Active | Bond state |
| 5 | `amount` | Bond Amount | Currency | | ✓ | | Bond value |
| 6 | `bank_name` | Bank Name | Data | | | | Issuing bank |
| 7 | `issue_date` | Issue Date | Date | | ✓ | Today | When issued |
| 8 | `expiry_date` | Expiry Date | Date | | ✓ | | Validity end |
| 9 | `bond_document` | Bond Document | Attach | | | | PDF/scan |
| 10 | `release_date` | Release Date | Date | | | | Depends on status=Released |
| 11 | `journal_entry` | Journal Entry (Issuance) | Link | Journal Entry | | | Read Only |
| 12 | `release_journal_entry` | Journal Entry (Release) | Link | Journal Entry | | | Read Only, depends on Released |
| 13 | `notes` | Notes | Text Editor | | | | Additional info |

---

## 🎯 Custom Buttons & UI Interactions

### Tender Opportunity Custom Buttons
The following custom buttons are available on the Tender Opportunity form (shown only when document is saved):

#### Collaborate Group
| Button | Action | Description |
|---|---|---|
| **Team & Tasks** | Opens dialog | Shows team members table and tasks with button to create new task |
| **Add Comment** | Opens dialog | Quick comment entry form (comment text + privacy checkbox) |
| **Create Default Tasks** | Server call | Manually triggers creation of 7 standard tasks |

#### Documents Group
| Button | Action | Description |
|---|---|---|
| **Generate Document** | Opens dialog | Select template → Generate PDF from template with placeholders |

#### Costing Group
| Button | Action | Description |
|---|---|---|
| **Create Cost Estimation** | New doc | Creates new Cost Estimation linked to this tender |
| **View All Estimations** | Navigation | Opens filtered list of all Cost Estimations for this tender |

#### Decision Group
| Button | Action | Description |
|---|---|---|
| **Create Decision Matrix** | New doc | Creates new Bid Decision Matrix |
| **View Decision Matrix** | Navigation | Opens filtered list of all Bid Decision Matrices |

#### Contract Group (Only when workflow_state = "Won")
| Button | Action | Description |
|---|---|---|
| **Create Performance Bond** | New doc | Creates Performance Bond with 10% of `final_contract_value` |
| **Manage Milestones** | Placeholder | Future feature for milestone management |

#### Standalone Button
| Button | Action | Description |
|---|---|---|
| **View Calendar** | Navigation | Opens Tender Calendar custom page |

---

### Custom Dialogs

#### 1. Team Management Dialog
**Triggered by**: "Team & Tasks" button  
**Features**:
- Displays team members in table format (User, Role, Assigned Date)
- Shows "Create New Task" button
- Auto-generates HTML from `team_members` child table

#### 2. Add Comment Dialog
**Triggered by**: "Add Comment" button  
**Fields**:
- `comment_text` (Text Editor, Required)
- `is_private` (Checkbox)

**Auto-sets**:
- `user`: Current logged-in user
- `timestamp`: Current datetime

#### 3. Generate Document Dialog
**Triggered by**: "Generate Document" button  
**Workflow**:
1. Loads all active Document Templates
2. User selects template
3. Calls `generate_from_template` server method
4. Shows generated content in preview dialog

#### 4. Generated Document Preview Dialog
**Features**:
- Large size dialog
- Displays rendered HTML with replaced placeholders
- "Download PDF" button triggers PDF generation and auto-links to tender

---

### Document Template Placeholder System

#### Available Placeholders
Templates use `{{placeholder}}` syntax (case-insensitive):

| Placeholder | Source | Example Value |
|---|---|---|
| `{{tender_title}}` | `title` | "Road Construction Project" |
| `{{organization}}` | `organization` | "Ministry of Works" |
| `{{tender_number}}` | `tender_number` | "MOW/2026/001" |
| `{{submission_deadline}}` | `submission_deadline` | "2026-03-15 14:00:00" |
| `{{final_bid_price}}` | `final_bid_price` | "5000000.00" |
| `{{sector}}` | `sector` | "Construction" |
| `{{tender_type}}` | `tender_type` | "Request for Proposal (RFP)" |
| `{{company_name}}` | System default | "BES" |

#### PDF Generation Flow
1. User selects template and generates preview
2. Clicks "Download PDF" in preview dialog
3. Server creates PDF using `get_pdf(html)`
4. Saves to File DocType with `is_private=1`
5. Auto-adds entry to `generated_documents` child table
6. Links: Template, File URL, Generated By, Date

---

### Child Table Auto-Calculations

#### Cost Item (on validate)
```
total_cost = quantity × unit_cost
```
**Event**: Triggers on every row save in parent Cost Estimation

#### Tender BOQ Item
**Note**: Currently has no auto-calculation (amount must be manually set or calculated via custom field formula)

---

## 6. Bid Security & Bid Security Request
**Naming**: `BSR-.YYYY.-.####` | **Submittable**: Yes | **Permissions**: System Manager, Tender Manager (Full)

### Business Logic & Accounting

#### Status Validation (on Validate)
- When `status` = "Issued", `security_number` is **mandatory**
  - Error: "Security Number is required when status is Issued"

#### Auto-Accounting (on Submit)
When document is submitted and `status` = "Issued":
1. **Auto-creates Journal Entry** if not already created
2. **Journal Entry Structure**:
   - Debit: Bid Bond Receivable Account (amount)
   - Credit: Bank Account (amount)
   - Reference Type: "Bid Security Request"
   - Cheque No: `security_number`

3. **Account Requirements**:
   - Must have a bank account linked
   - Must have "Bid Bond Receivable" account in Chart of Accounts

#### Event Handlers
- `validate()`: Enforces security_number requirement
- `on_submit()`: Triggers `create_journal_entry()` for accounting

---

### Bid Security Request
| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `naming_series` | Series | Select | BSR-.YYYY.-.#### | ✓ | | Auto-naming |
| 2 | `tender` | Tender Opportunity | Link | Tender Opportunity | ✓ | | Parent tender |
| 3 | `organization` | Organization | Data | | | | Fetched from tender, Read Only |
| 4 | `type` | Security Type | Select | CPO, Bank Guarantee, Insurance Bond, Letter of Credit | ✓ | CPO | Security type |
| 5 | `status` | Status | Select | Draft, Requested, Issued, Returned, Forfeited | ✓ | Draft | Request state |
| 6 | `bank_account` | Source Bank Account | Link | Account | ✓ | | ERP account |
| 7 | `amount` | Amount | Currency | | ✓ | | Bond amount |
| 8 | `validity_period_days` | Validity (Days) | Int | | ✓ | 90 | Default 90 |
| 9 | `required_date` | Required By Date | Date | | ✓ | | Deadline |
| 10 | `security_number` | Security / CPO Number | Data | | | | Issued number |
| 11 | `expiry_date` | Expiry Date | Date | | | | Validity end |
| 12 | `journal_entry` | Journal Entry (Auto) | Link | Journal Entry | | | Read Only |
| 13 | `prepared_by` | Prepared By | Link | User | ✓ | | ISO role |
| 14 | `checked_by` | Checked By | Link | User | | | ISO role |
| 15 | `approved_by` | Approved By | Link | User | | | ISO role |

---

## 7. Competitor (Master)
**Naming**: By `competitor_name` field | **Permissions**: Tender User, Tender Manager (Full)

| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `competitor_name` | Competitor Name | Data | | ✓ | | Unique, naming field |
| 2 | `company_type` | Company Type | Select | Local, International, Joint Venture | | | Entity type |
| 3 | `sector` | Primary Sector | Select | Construction, Electro-Mechanical, Maintenance, etc. | | | Specialization |
| 4 | `contact_person` | Contact Person | Data | | | | Key contact |
| 5 | `phone` | Phone | Data | | | | Phone number |
| 6 | `email` | Email | Data (Email) | | | | Email address |
| 7 | `website` | Website | Data (URL) | | | | Website URL |
| 8 | `strengths` | Known Strengths | Small Text | | | | Competitive advantages |
| 9 | `weaknesses` | Known Weaknesses | Small Text | | | | Vulnerabilities |
| 10 | `typical_pricing_strategy` | Pricing Strategy | Select | Aggressive (Low Price), Competitive, Premium | | | Pricing approach |
| 11 | `notes` | Notes | Text Editor | | | | Additional intelligence |

---

## 8. Document Template
**Naming**: By `template_name` field | **Permissions**: Tender Manager (Full), Tender User (Read)

| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `template_name` | Template Name | Data | | ✓ | | Unique, naming field |
| 2 | `category` | Category | Select | Cover Letter, Technical Proposal, Financial Proposal, etc. | ✓ | | Template type |
| 3 | `is_active` | Active | Check | | | 1 | Enabled/disabled |
| 4 | `content` | Content | HTML Editor | | ✓ | | Template HTML with {{placeholders}} |
| 5 | `placeholders_help` | Placeholder Guide | Text | | | | Read Only, help text |
| 6 | `usage_notes` | Usage Notes | Small Text | | | | Instructions |

---

## 9. Tender Content Library
**Naming**: By `title` field | **Permissions**: System Manager, Tender Manager (Full)

| # | Fieldname | Label | Type | Options | Required | Default | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `title` | Title | Data | | ✓ | | In List View |
| 2 | `category` | Category | Select | Company Policy, Team Bio, Case Study, Product Spec, Compliance, Methodology, Template Answer | ✓ | | Content type |
| 3 | `status` | Status | Select | Draft, Verified, Archived | ✓ | Draft | Review status |
| 4 | `content_owner` | Content Owner | Link | User | | | Responsible person |
| 5 | `last_updated` | Last Updated | Date | | | | Last edit date |
| 6 | `keywords` | Keywords (Tags) | Small Text | | | | Search tags |
| 7 | `content` | Content Body | Text Editor | | | | Reusable content |

---

## 10. Child Table Forms

### Cost Item (Parent: Cost Estimation)

**Business Logic**: Auto-calculates `total_cost` on validate event.

| # | Fieldname | Label | Type | Options | Required | In List View | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `item_code` | Item Code | Link | Item | | ✓ | ERP Item Master |
| 2 | `item_name` | Item Name | Data | | ✓ | ✓ | Fetched from item_code |
| 3 | `description` | Description | Small Text | | | | Details |
| 4 | `quantity` | Quantity | Float | | ✓ | ✓ | Qty |
| 5 | `uom` | UOM | Link | UOM | | | Fetched from item_code |
| 6 | `unit_cost` | Unit Cost | Currency | | ✓ | ✓ | Price per unit |
| 7 | `total_cost` | Total Cost | Currency | | | ✓ | Read Only, calculated |
| 8 | `supplier_quotation` | Supplier Quotation | Link | Supplier Quotation | | | Reference |
| 9 | `notes` | Notes | Small Text | | | | Additional info |

### Tender Team Member (Parent: Tender Opportunity)
| # | Fieldname | Label | Type | Options | Required | In List View | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `user` | Team Member | Link | User | ✓ | ✓ | Team member |
| 2 | `role` | Role | Select | Technical Lead, Financial Analyst, Legal Reviewer, Proposal Manager, Project Manager, SME, Quality Reviewer | ✓ | ✓ | Responsibility |
| 3 | `assigned_date` | Assigned Date | Date | | | ✓ | Default: Today |
| 4 | `responsibilities` | Responsibilities | Small Text | | | | Task description |

### Tender BOQ Item (Parent: Tender Opportunity)
| # | Fieldname | Label | Type | Options | Required | In List View | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `item_code` | Item Code | Link | Item | | ✓ | ERP Item |
| 2 | `description` | Description | Small Text | | ✓ | ✓ | Item description |
| 3 | `uom` | UOM | Link | UOM | | ✓ | Unit of measure |
| 4 | `qty` | Quantity | Float | | ✓ | ✓ | Quantity |
| 5 | `rate` | Rate | Currency | | | ✓ | Price per unit |
| 6 | `amount` | Amount | Currency | | | ✓ | Read Only, calculated |

### Contract Milestone (Parent: Performance Bond / Tender Opportunity)
| # | Fieldname | Label | Type | Options | Required | In List View | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `milestone_name` | Milestone Name | Data | | ✓ | ✓ | Milestone title |
| 2 | `description` | Description | Small Text | | | | Details |
| 3 | `due_date` | Due Date | Date | | | ✓ | Target completion |
| 4 | `completion_date` | Completion Date | Date | | | | Actual completion |
| 5 | `status` | Status | Select | Pending, In Progress, Completed, Delayed | | ✓ | Default: Pending |
| 6 | `payment_amount` | Payment Amount | Currency | | | ✓ | Payment value |
| 7 | `payment_percentage` | Payment % | Percent | | | | % of total |
| 8 | `invoice_raised` | Invoice Raised | Check | | | | Default: 0 |
| 9 | `payment_received` | Payment Received | Check | | | | Default: 0 |

### Proposal Section (Parent: Tender Opportunity)
| # | Fieldname | Label | Type | Options | Required | In List View | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `section_name` | Section Name | Data | | ✓ | ✓ | Section title |
| 2 | `owner_user` | Owner | Link | User | | ✓ | Responsible person |
| 3 | `weighting` | Weighting | Percent | | | | Score weight |
| 4 | `status` | Status | Select | Pending, Draft, Review, Complete | | ✓ | Default: Pending |
| 5 | `key_message` | Key Message / Theme | Small Text | | | ✓ | Main message |
| 6 | `customer_issues` | Customer Issues Addressed | Small Text | | | | Pain points |
| 7 | `proposed_solution_section` | Proposed Solution (Section) | Text Editor | | | | Solution detail |
| 8 | `evidence_required` | Evidence / Case Studies Required | Small Text | | | | Supporting docs |
| 9 | `word_count_limit` | Word Count Limit | Int | | | | Max words |
| 10 | `complexity` | Complexity | Select | Low, Medium, High | | ✓ | Default: Medium |
| 11 | `instructions` | Instructions | Small Text | | | | Writing instructions |

### Bid Decision Factor (Parent: Tender Opportunity)
| # | Fieldname | Label | Type | Options | Required | In List View | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `factor` | Decision Factor | Data | | ✓ | ✓ | Factor name |
| 2 | `score` | Score (0-5) | Int | | ✓ | ✓ | Default: 3 |
| 3 | `weight` | Weight (%) | Percent | | | ✓ | Default: 20 |

### Clarification Question (Parent: Tender Opportunity)
| # | Fieldname | Label | Type | Options | Required | In List View | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `question` | Question | Text | | ✓ | ✓ | Question text |
| 2 | `answer` | Answer | Text | | | | Client response |
| 3 | `date_asked` | Date Asked | Date | | ✓ | ✓ | When asked |
| 4 | `status` | Status | Select | Pending, Answered | | ✓ | Default: Pending |

### Tender Comment (Parent: Tender Opportunity)
| # | Fieldname | Label | Type | Options | Required | In List View | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `user` | User | Link | User | | ✓ | Default: current user, Read Only |
| 2 | `user_full_name` | Name | Data | | | ✓ | Fetched, Read Only |
| 3 | `timestamp` | Timestamp | Datetime | | | ✓ | Default: Now, Read Only |
| 4 | `is_private` | Private Comment | Check | | | | Default: 0 |
| 5 | `comment_text` | Comment | Text Editor | | ✓ | | Comment body |

### Tender Competitor (Parent: Tender Opportunity)
| # | Fieldname | Label | Type | Options | Required | In List View | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `competitor_name` | Competitor Name | Data | | ✓ | ✓ | Competitor name |
| 2 | `bid_price` | Their Bid Price | Currency | | | ✓ | Their price |
| 3 | `notes` | Strengths/Weaknesses | Small Text | | | | Intelligence notes |
| 4 | `is_winner` | Winner? | Check | | | ✓ | Default: 0 |

### Tender Generated Document (Parent: Tender Opportunity)
| # | Fieldname | Label | Type | Options | Required | In List View | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `template` | Template | Link | Document Template | ✓ | ✓ | Source template |
| 2 | `file` | Generated PDF | Attach | | ✓ | ✓ | Output file |
| 3 | `generated_by` | Generated By | Link | User | ✓ | ✓ | Who generated |
| 4 | `date` | Generation Date | Datetime | ✓ | ✓ | When generated |
| 5 | `print_pdf` | Print PDF | Button | | | ✓ | Action button |

---

## 📊 Summary Statistics
- **Total DocTypes**: 20
- **Total Fields in Tender Opportunity**: 107
- **Total Child Tables**: 10
- **Total Standalone Forms**: 9
- **Workflows**: 2 (Two-Stage Tender Approval, Tender Register Workflow)

---

## 🔗 Field Relationships & Dependencies

### Fetch Relationships (Auto-Populated Fields)
These fields automatically pull data from linked documents:

#### Tender Opportunity
| Field | Fetched From | Source Field |
|---|---|---|
| `bond_status` | `bid_security_request` | `status` |
| `bond_number` | `bid_security_request` | `security_number` |
| `cpo_journal_entry` | `bid_security_request` | `journal_entry` |

#### Bid Security Request
| Field | Fetched From | Source Field |
|---|---|---|
| `organization` | `tender` → `Tender Opportunity` | `organization` |

#### Cost Item (Child Table)
| Field | Fetched From | Source Field |
|---|---|---|
| `item_name` | `item_code` → `Item` | `item_name` |
| `uom` | `item_code` → `Item` | `stock_uom` |

#### Tender Comment (Child Table)
| Field | Fetched From | Source Field |
|---|---|---|
| `user_full_name` | `user` → `User` | `full_name` |

---

### Conditional Field Display (depends_on)
Fields that only appear under specific conditions:

#### Tender Opportunity
| Field | Appears When |
|---|---|
| `completion_date` (Task) | `status` == "Completed" |
| `completion_notes` (Task) | `status` == "Completed" |
| `release_date` (Performance Bond) | `status` == "Released" |
| `release_journal_entry` (Performance Bond) | `status` == "Released" |

#### Bid Decision Matrix
| Field | Appears When |
|---|---|
| `no_bid_reason` | `decision` == "No-Bid" |

---

### Computed Fields (Read-Only, Auto-Calculated)

#### Cost Estimation
- `total_direct_cost`: Sum of `items[].total_cost`
- `overhead_amount`: Calculated from `overhead_percentage`
- `profit_amount`: Calculated from `profit_margin_percentage`
- `total_price`: Final calculated price (bold display)

#### Bid Decision Matrix
- `total_score`: Sum of 7 scoring criteria
- `suggested_decision`: "Bid" or "No-Bid" based on score threshold

#### Cost Item (Child Table)
- `total_cost`: `quantity` × `unit_cost`

#### Tender BOQ Item (Child Table)
- `amount`: `qty` × `rate`

---

### Link Field Cascades
When you link these documents, related fields auto-populate:

1. **Tender Opportunity** → **Bid Security Request**
   - Creates auto-link when workflow_state = "Tender Purchased"
   - Populates: `type`, `amount`, `validity_period_days`, `bank_account`, `required_date`

2. **Item Master** → **Cost Item**
   - Fetches: `item_name`, `stock_uom`

3. **User** → **Tender Comment**
   - Fetches: `full_name`
   - Auto-sets: current `user`, `timestamp`

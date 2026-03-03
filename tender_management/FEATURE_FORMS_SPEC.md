# Tender Management - Exhaustive Feature Forms Specification

This document provides a low-level technical specification of every DocType form within the Tender Management module.

---

## 📑 Index
1. [Tender Opportunity](#tender-opportunity) (Main Hub)
2. [Standalone Forms](#standalone-forms)
3. [Child Table Forms](#child-table-forms)
4. [Lifecycle & Workflows](#lifecycle--workflows)

---

## 🛠️ 1. Tender Opportunity
The central DocType governing the tender lifecycle.

**Type**: Standalone | **Naming**: `T-OPP-.YYYY.-.####` (Naming Series) | **Module**: Tender Management

| Label | Fieldname | Type | Options / Default | Reqd |
| :--- | :--- | :--- | :--- | :--- |
| Series | `naming_series` | Select | T-OPP-.YYYY.-.####, etc. | Yes |
| Tender Title | `title` | Data | | Yes |
| Organization | `organization` | Data | | Yes |
| Sector | `sector` | Select | Construction, etc. | Yes |
| Tender Type | `tender_type` | Select | RFP, RFQ, ITT, etc. | Yes |
| Workflow State | `workflow_state` | Link | Workflow State (Read Only) | No |
| Status | `status` | Select | Open, Closed | No |
| Submission Deadline | `submission_deadline`| Datetime | | Yes |
| Bid Probability | `bid_probability_score`| Percent | | No |
| Items | `items` | Table | Tender BOQ Item | No |
| Team Members | `team_members` | Table | Tender Team Member | No |
| Comments | `comments` | Table | Tender Comment | No |

---

## 📄 2. Standalone Forms

### **Tender Task**
Assign and track specific assignments.
**Naming**: `TASK-{tender}-{####}`

| Label | Fieldname | Type | Options / Default | Reqd |
| :--- | :--- | :--- | :--- | :--- |
| Tender | `tender` | Link | Tender Opportunity | Yes |
| Task Title | `title` | Data | | Yes |
| Assigned To | `assigned_to` | Link | User | Yes |
| Due Date | `due_date` | Date | | Yes |
| Status | `status` | Select | Open, In Progress, Complete | Yes |
| Priority | `priority` | Select | Low, Medium, High, Urgent | No |

---

### **Cost Estimation**
Full BOQ builder and margin calculator.
**Naming**: `CE-{tender}-{####}`

| Label | Fieldname | Type | Options / Default | Reqd |
| :--- | :--- | :--- | :--- | :--- |
| Tender | `tender` | Link | Tender Opportunity | Yes |
| Status | `status` | Select | Draft, Review, Approved | No |
| Items | `items` | Table | Cost Item | No |
| Total Direct Cost| `total_direct_cost`| Currency | Read Only | No |
| Overhead % | `overhead_percentage`| Percent | Default: 15 | No |
| Profit Margin % | `profit_margin_percentage`| Percent | Default: 10 | No |
| Total Price | `total_price` | Currency | Read Only (Bold) | No |

---

### **Bid Decision Matrix**
Structured Go/No-Go evaluation framework.
**Naming**: `BDM-{tender}-{####}`

| Label | Fieldname | Type | Options / Default | Reqd |
| :--- | :--- | :--- | :--- | :--- |
| Tender | `tender` | Link | Tender Opportunity | Yes |
| Decision | `decision` | Select | Pending, Bid, No-Bid | Yes |
| Win Prob Score | `win_probability_score`| Int | 0-10 | No |
| Strategic Fit | `strategic_fit_score` | Int | 0-10 | No |
| Total Score | `total_score` | Int | Read Only | No |
| Suggested Decision| `suggested_decision` | Data | Read Only | No |

---

### **Performance Bond**
Tracks post-award securities and Milestones.
**Naming**: `PB-{tender}-{####}`

| Label | Fieldname | Type | Options / Default | Reqd |
| :--- | :--- | :--- | :--- | :--- |
| Tender | `tender` | Link | Tender Opportunity | Yes |
| Bond Number | `bond_number` | Data | | Yes |
| Bond Type | `bond_type` | Select | Performance, Advance, etc. | No |
| Amount | `amount` | Currency | | Yes |
| Bank Name | `bank_name` | Data | | No |
| Expiry Date | `expiry_date` | Date | | Yes |

---

### **Bid Security Request**
Formal request for Bid Bonds (ISO 9001).
**Naming**: `BSR-.YYYY.-.####`

| Label | Fieldname | Type | Options / Default | Reqd |
| :--- | :--- | :--- | :--- | :--- |
| Tender | `tender` | Link | Tender Opportunity | Yes |
| Status | `status` | Select | Draft, Requested, Issued | Yes |
| Amount | `amount` | Currency | | Yes |
| Bank Account | `bank_account` | Link | Account | Yes |
| Prepared By | `prepared_by` | Link | User | Yes |

---

### **Competitor**
Intelligence database for rivals.
**Naming**: `field:competitor_name`

| Label | Fieldname | Type | Options / Default | Reqd |
| :--- | :--- | :--- | :--- | :--- |
| Competitor Name | `competitor_name` | Data | Unique | Yes |
| Company Type | `company_type` | Select | Local, International, JV | No |
| Pricing Strategy| `typical_pricing_strategy`| Select | Aggressive, Premium, etc.| No |

---

### **Document Template**
Markdown/HTML formatting engine.
**Naming**: `field:template_name`

| Label | Fieldname | Type | Options / Default | Reqd |
| :--- | :--- | :--- | :--- | :--- |
| Template Name | `template_name` | Data | | Yes |
| Category | `category` | Select | Cover Letter, Proposal, etc. | Yes |
| Content | `content` | HTML Editor | Jinja tags supported | Yes |

---

### **Tender Content Library**
Technical snippet repository.
**Naming**: `Data` (Title)

| Label | Fieldname | Type | Options / Default | Reqd |
| :--- | :--- | :--- | :--- | :--- |
| Title | `title` | Data | | Yes |
| Category | `category` | Select | Policy, Bio, Spec, etc. | Yes |
| Content Body | `content` | Text Editor | | No |

---

## 🔗 3. Child Table Forms
These forms are used within the standalone DocTypes listed above.

### **Cost Item** (Parent: Cost Estimation)
| Label | Fieldname | Type | Options | Reqd |
| :--- | :--- | :--- | :--- | :--- |
| Item Code | `item_code` | Link | Item | No |
| Quantity | `quantity` | Float | | Yes |
| Unit Cost | `unit_cost` | Currency | | Yes |
| Total Cost | `total_cost` | Currency | Read Only | No |

### **Tender Team Member** (Parent: Tender Opportunity)
| Label | Fieldname | Type | Options | Reqd |
| :--- | :--- | :--- | :--- | :--- |
| Team Member | `user` | Link | User | Yes |
| Role | `role` | Select | Technical Lead, FM, etc. | Yes |

### **Tender BOQ Item** (Parent: Tender Opportunity)
| Label | Fieldname | Type | Options | Reqd |
| :--- | :--- | :--- | :--- | :--- |
| Description | `description` | Small Text | | Yes |
| Quantity | `qty` | Float | | Yes |
| Rate | `rate` | Currency | | No |

### **Contract Milestone** (Parent: Performance Bond / Opportunity)
| Label | Fieldname | Type | Options | Reqd |
| :--- | :--- | :--- | :--- | :--- |
| Milestone Name | `milestone_name` | Data | | Yes |
| Status | `status` | Select | Pending, Complete, etc. | No |
| Payment Amount | `payment_amount` | Currency | | No |

---

## 🔄 4. Lifecycle & Workflows
The forms are governed by two primary workflows:

1.  **Two-Stage Tender Approval**:
    *   **States**: Draft -> Capture Plan -> Bid/No Bid -> Plan Proposal -> Kick Off -> Develop -> Evaluation -> Won/Lost -> Lessons Learned.
    *   **Roles**: Tender User, Tender Manager, Tender Director.

2.  **Tender Register Workflow**:
    *   **States**: Identify -> Qualify -> Plan -> Proposal -> Submitted -> Negotiation -> Won/Lost.
    *   **Roles**: System Manager.

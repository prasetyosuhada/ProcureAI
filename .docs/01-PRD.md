# Product Requirements Document (PRD)

# ProcureAI — Requirement & Demand Analysis

**Document Status:** Draft
**Version:** 1.0
**Scope:** Requirement Clarification and Demand Analysis
**Product Type:** Agentic AI Procurement Assistant

---

## 1. Product Overview

ProcureAI is an Agentic AI system designed to help employees transform an unstructured purchasing need into a structured and justified **Purchase Requisition (PR)**.

Instead of requiring users to understand procurement terminology and manually complete numerous fields, users can describe their needs using natural language.

The system uses LLM-powered agents to:

1. Understand the user's purchasing intent.
2. Ask relevant clarification questions.
3. Transform the conversation into a structured requirement.
4. Analyze whether the requested demand is reasonable based on available organizational data.
5. Recommend the appropriate purchase quantity.
6. Generate a PR draft for user review and submission.

The current scope intentionally stops at **PR creation**.

Vendor sourcing, RFQ, negotiation, contract management, PO creation, invoice processing, and other downstream procurement activities are outside the MVP scope but are part of the broader Enterprise Procurement AI roadmap.

---

# 2. Background & Problem Statement

Traditional procurement systems such as ERP platforms generally require users to manually provide structured information.

A typical Purchase Requisition may require:

* Item
* Category
* Quantity
* Unit of Measure
* Specification
* Required Date
* Department
* Cost Center
* Budget
* Business Justification
* Attachments

This approach works well when the requester already knows exactly what they need.

However, requesters are often business users who understand the **business need**, rather than the exact procurement specification.

For example:

> "I need laptops for our new backend development team."

The requester may not know:

* Which specification is appropriate.
* How much RAM is required.
* Whether existing assets can satisfy the requirement.
* Whether there are already open purchase requests.
* Whether the requested quantity is reasonable.

The current process therefore places much of the burden on the requester.

---

# 3. Product Vision

The vision is to provide a **conversational procurement entry point** where employees can describe their needs naturally, while AI assists in transforming those needs into procurement-ready information.

The intended experience is:

```text
Business Need
      ↓
Natural Language Conversation
      ↓
Requirement Clarification
      ↓
Structured Requirement
      ↓
Demand Analysis
      ↓
Demand Recommendation
      ↓
PR Draft
      ↓
User Review
      ↓
Submit PR
```

The AI does not replace the ERP/procurement system.

Instead:

> **ERP remains the system of record, while AI acts as the intelligence layer between the user and the procurement workflow.**

---

# 4. Goals

## 4.1 Primary Goals

### G1 — Understand Natural-Language Procurement Requests

Allow users to describe what they need without requiring them to understand procurement forms or terminology.

Example:

> "We are hiring 10 backend developers next month and need laptops for them."

The system should understand the underlying purchasing intent.

---

### G2 — Identify Missing Information

The system should determine which information is required before a valid PR can be created.

For example:

```text
User:
I need laptops for my new team.

Agent:
How many employees will need laptops?
```

The agent should avoid asking unnecessary questions.

---

### G3 — Generate Structured Requirements

The conversational input should be transformed into structured procurement information.

Example:

```json
{
  "category": "IT Equipment",
  "item": "Laptop",
  "quantity": 10,
  "purpose": "Backend Development",
  "required_date": "2026-09-01",
  "requirements": {
    "ram": "32GB",
    "storage": "1TB"
  }
}
```

---

### G4 — Analyze Demand

The system should analyze the requested demand using available organizational data.

Relevant information may include:

* Existing inventory
* Existing assets
* Purchase history
* Open PRs
* Open POs
* Usage/consumption data
* Available budget

The goal is to determine whether the requested quantity is reasonable.

---

### G5 — Provide an Explainable Recommendation

The system should not simply modify the user's requested quantity.

It should explain the reasoning.

Example:

> You requested 10 laptops. Five laptops are expected to become available from existing assets next month. Based on this information, we recommend purchasing 5 new laptops.

---

### G6 — Generate a PR Draft

Once the requirement has been clarified and analyzed, the system should generate a structured PR draft.

The user should be able to review and edit the result before submitting it.

---

# 5. Non-Goals

The following capabilities are **not included in the current scope**:

* Vendor discovery
* Vendor comparison
* RFQ generation
* RFQ analysis
* Sourcing strategy
* Negotiation
* Contract review
* Supplier onboarding
* Supplier risk assessment
* Supplier performance management
* PO generation
* Invoice processing
* Invoice matching
* Payment processing
* Strategic procurement planning

These capabilities belong to the broader Enterprise Procurement AI roadmap.

---

# 6. Target Users

## 6.1 Requester

Employees who need to purchase goods or services.

Examples:

* Engineering
* HR
* Finance
* Operations
* Marketing
* IT
* Facilities

The requester does not necessarily have procurement expertise.

---

## 6.2 Procurement Team

Procurement users who may review or process the resulting PR.

The current MVP does not automate the entire procurement team's workflow.

---

## 6.3 Approver

Managers or budget owners responsible for approving submitted PRs.

Approval itself is outside the AI MVP scope.

---

# 7. High-Level Architecture

```text
                           USER
                             │
                             ▼
              ┌────────────────────────────┐
              │ Procurement Copilot        │
              │ Orchestrator Agent         │
              └──────────────┬─────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
     ┌──────────────────────┐  ┌──────────────────────┐
     │ Requirement          │  │ Demand Analysis      │
     │ Clarification Agent  │  │ Agent                │
     └──────────┬───────────┘  └──────────┬───────────┘
                │                         │
                ▼                         ▼
             Skills                    Skills
                │                         │
                ▼                         ▼
             Tools                     Tools
                │                         │
                └────────────┬────────────┘
                             ▼
                        PR Draft
                             │
                             ▼
                        User Review
                             │
                             ▼
                        Submit PR
```

---

# 8. Agent Architecture

## 8.1 Procurement Copilot Orchestrator

### Responsibility

The Orchestrator controls the overall workflow.

It should:

* Receive the initial user request.
* Determine the current state of the request.
* Invoke Requirement Clarification when information is insufficient.
* Invoke Demand Analysis after the requirement is sufficiently complete.
* Handle user clarification loops.
* Combine outputs from downstream agents.
* Produce the final PR draft.

### The Orchestrator should NOT:

* Directly perform detailed requirement analysis.
* Directly query databases.
* Make deterministic business-rule decisions itself.
* Replace the specialized agents.

---

# 9. Requirement Clarification Agent

## 9.1 Purpose

Transform an ambiguous natural-language purchasing request into a sufficiently complete structured requirement.

### Example

Input:

> "I need laptops for our new development team."

The agent may ask:

> How many developers will need laptops?

Then:

> Will they primarily work on backend, frontend, mobile, or data workloads?

Then:

> When are the laptops required?

---

## 9.2 Skills

### Requirement Interview Skill

Responsible for conversational discovery.

Capabilities:

* Identify missing information.
* Ask contextual questions.
* Avoid unnecessary questions.
* Maintain conversation context.

---

### Requirement Extraction Skill

Transform natural language into structured fields.

Example:

```text
Natural Language
        ↓
Structured Requirement
```

---

### Requirement Validation Skill

Validate the extracted requirement.

Examples:

* Quantity is valid.
* Required date is valid.
* Required fields are present.
* Requirements do not contradict each other.

---

### Requirement Summarization Skill

Generate a human-readable summary for user confirmation.

Example:

```text
Purchase Requirement

Item:
Laptop

Quantity:
10

Purpose:
Backend Development

RAM:
32 GB

Storage:
1 TB

Required Date:
September 1, 2026
```

---

## 9.3 Tools

### Procurement Category Tool

Retrieves available procurement categories.

Example:

```text
Laptop
    ↓
IT Equipment
```

---

### Item Specification Tool

Retrieves organizational standards or predefined specifications.

Example:

```text
Company Standard Laptop

Minimum RAM: 16 GB
Minimum Storage: 512 GB
```

---

### Procurement Policy Tool

Retrieves relevant procurement policies that affect the requirement.

Example:

```text
Laptop purchases above a certain value
require additional justification.
```

The tool provides factual policy information; the LLM reasons about how the policy applies.

---

# 10. Demand Analysis Agent

## 10.1 Purpose

Determine whether the requested demand is reasonable based on available organizational information.

The Demand Analysis Agent does not determine which vendor should be used.

It answers:

> **"How much should actually be purchased?"**

---

## 10.2 Example

User requests:

```text
10 laptops
```

Available organizational data:

```text
Existing unused assets: 2
Assets becoming available next month: 3
Open PRs: 0
Open POs: 0
```

The agent may recommend:

```text
Requested quantity: 10

Existing/expected available:
5

Recommended new purchase:
5
```

---

## 10.3 Skills

### Demand Assessment Skill

Analyze demand using available organizational data.

---

### Demand Validation Skill

Validate the requested demand against:

* Existing resources
* Existing requests
* Existing orders
* Historical purchasing
* Consumption patterns

---

### Demand Recommendation Skill

Generate a recommended purchase quantity or identify that the requested quantity is reasonable.

---

### Demand Explanation Skill

Explain why the recommendation differs from the original request.

Example:

> Five existing assets can satisfy part of the requirement, so only five new units are recommended.

---

# 11. Demand Analysis Tools

## Inventory Tool

Retrieves current inventory.

Example:

```text
get_current_stock(item)
```

---

## Asset Tool

Retrieves existing organizational assets.

Example:

```text
get_available_assets(category)
get_assigned_assets(category)
get_returning_assets(category)
```

---

## Purchase History Tool

Retrieves historical purchases.

Example:

```text
get_purchase_history(item)
```

---

## Open PR Tool

Retrieves existing purchase requests.

Example:

```text
get_open_purchase_requests(item)
```

---

## Open PO Tool

Retrieves existing purchase orders.

Example:

```text
get_open_purchase_orders(item)
```

---

## Usage / Demand Tool

Retrieves historical consumption or usage information.

Example:

```text
get_consumption_history(item)
```

---

## Budget Tool

Retrieves available budget information.

Example:

```text
get_available_budget(cost_center)
```

Budget information is contextual information for the analysis and does not replace the organization's deterministic budget validation and approval process.

---

# 12. End-to-End User Flow

## Step 1 — User Starts a Request

User provides a natural-language request.

Example:

> "I need laptops for 10 new backend developers joining next month."

---

## Step 2 — Requirement Clarification

The Orchestrator invokes the Requirement Clarification Agent.

The agent identifies missing information.

Example:

```text
Agent:
What minimum specifications are required?

User:
They will run Docker and several backend services locally.

Agent:
When are the laptops required?

User:
Before September 1.
```

---

## Step 3 — Requirement Confirmation

The system summarizes:

```text
Item:
Laptop

Quantity:
10

Users:
Backend Developers

Workload:
Docker / Backend Development

Required Date:
September 1

Suggested Specification:
32 GB RAM
1 TB SSD
```

User confirms or edits the requirement.

---

## Step 4 — Demand Analysis

The Orchestrator invokes the Demand Analysis Agent.

The agent calls relevant tools:

```text
Inventory Tool
Asset Tool
Purchase History Tool
Open PR Tool
Open PO Tool
Usage Tool
```

---

## Step 5 — Demand Recommendation

Example:

```text
Requested:
10 laptops

Available existing assets:
3

Expected returning assets:
2

Recommended purchase:
5 laptops
```

The agent explains the recommendation.

---

## Step 6 — User Confirmation

The user can:

```text
[Accept Recommendation]
[Keep Original Quantity]
[Edit Requirement]
```

---

## Step 7 — PR Draft

The system creates:

```text
Purchase Requisition

Category:
IT Equipment

Item:
Laptop

Quantity:
5

Specification:
32 GB RAM
1 TB SSD

Required Date:
September 1, 2026

Business Justification:
Equipment required for new backend development team.

AI Demand Analysis:
5 existing/returning assets can satisfy part of the requested demand.
```

---

## Step 8 — User Review

The user reviews the generated PR.

```text
[Edit]
[Submit PR]
```

---

## Step 9 — PR Submission

The PR is submitted to the existing procurement/ERP system.

The current AI scope ends here.

---

# 13. Important Business Boundary

The system should clearly separate:

### Demand Decision

Before PR approval:

> "What do we actually need?"

Handled by:

**Requirement Clarification + Demand Analysis**

from:

### Sourcing Decision

After PR approval:

> "How should we procure it?"

Handled by future capabilities such as:

* Procurement Planner
* Vendor Discovery
* Vendor Comparison
* RFQ
* Negotiation
* Purchase Recommendation

Therefore, the current MVP should **not determine the vendor or procurement method**.

---

# 14. Agent / Skill / Tool Responsibility

| Layer        | Component                        | Responsibility                          |
| ------------ | -------------------------------- | --------------------------------------- |
| Orchestrator | Procurement Copilot Orchestrator | Workflow coordination                   |
| Agent        | Requirement Clarification Agent  | Understand user requirement             |
| Agent        | Demand Analysis Agent            | Analyze actual demand                   |
| Skill        | Requirement Interview            | Ask clarification questions             |
| Skill        | Requirement Extraction           | Convert conversation to structured data |
| Skill        | Requirement Validation           | Validate requirement                    |
| Skill        | Requirement Summarization        | Summarize requirement                   |
| Skill        | Demand Assessment                | Analyze demand                          |
| Skill        | Demand Validation                | Validate demand                         |
| Skill        | Demand Recommendation            | Recommend quantity                      |
| Skill        | Demand Explanation               | Explain recommendation                  |
| Tool         | Category Tool                    | Retrieve categories                     |
| Tool         | Specification Tool               | Retrieve specifications                 |
| Tool         | Policy Tool                      | Retrieve procurement policy             |
| Tool         | Inventory Tool                   | Retrieve inventory                      |
| Tool         | Asset Tool                       | Retrieve assets                         |
| Tool         | Purchase History Tool            | Retrieve purchase history               |
| Tool         | Open PR Tool                     | Retrieve open PRs                       |
| Tool         | Open PO Tool                     | Retrieve open POs                       |
| Tool         | Usage/Demand Tool                | Retrieve usage data                     |
| Tool         | Budget Tool                      | Retrieve budget information             |

### Sub-agents

**None in the current scope.**

The two specialized agents are sufficiently bounded and do not currently require additional autonomous agents.

---

# 15. Functional Requirements

## FR-01 — Natural Language Request

The system shall allow users to describe purchasing needs using natural language.

---

## FR-02 — Requirement Discovery

The system shall identify missing information required to create a meaningful purchase requirement.

---

## FR-03 — Conversational Clarification

The system shall ask users contextual clarification questions.

---

## FR-04 — Structured Requirement Extraction

The system shall convert conversation results into structured procurement data.

---

## FR-05 — Requirement Validation

The system shall detect incomplete or contradictory requirements.

---

## FR-06 — Requirement Confirmation

The system shall allow users to review and confirm the structured requirement.

---

## FR-07 — Demand Data Retrieval

The system shall retrieve relevant organizational data required for demand analysis.

---

## FR-08 — Demand Analysis

The system shall analyze the requested demand against available organizational information.

---

## FR-09 — Demand Recommendation

The system shall provide a recommended purchase quantity when sufficient information is available.

---

## FR-10 — Explainable Recommendation

The system shall explain the reasoning behind its demand recommendation.

---

## FR-11 — User Override

Users shall be able to reject or modify the AI recommendation.

---

## FR-12 — PR Generation

The system shall generate a structured PR draft from the confirmed requirement and demand recommendation.

---

## FR-13 — PR Submission

The system shall support submission of the PR to the procurement/ERP system.

---

# 16. Non-Functional Requirements

## Explainability

AI recommendations must provide supporting reasons and relevant data sources.

---

## Deterministic Data

The system must retrieve factual organizational data through tools rather than asking the LLM to infer or invent such information.

---

## Human-in-the-Loop

The system must not silently modify the user's requirement.

Users must be able to review and override recommendations.

---

## Auditability

The system should record:

* User request
* Clarification conversation
* Structured requirement
* Tools invoked
* Data retrieved
* AI recommendation
* User modification
* Final PR

---

## Reliability

The system should clearly indicate when required information is unavailable rather than generating unsupported assumptions.

---

## Security

The system must respect user authorization when accessing:

* Budget information
* Purchase history
* Inventory
* Assets
* Procurement policies
* Existing PRs and POs

---

# 17. Success Metrics

### Requirement Completion Rate

Percentage of requests that reach a complete structured requirement.

---

### Clarification Efficiency

Average number of clarification turns required before a requirement becomes complete.

---

### PR Preparation Time

Reduction in time required to prepare a PR compared with the existing manual process.

---

### Demand Recommendation Acceptance

Percentage of AI recommendations accepted by users.

---

### PR Correction Rate

Percentage of AI-generated PRs requiring significant manual correction.

---

### User Satisfaction

Requester satisfaction with the AI-assisted PR creation process.

---

# 18. Example User Experience

### User

> I need laptops for my new development team.

### AI

> How many team members will need laptops?

### User

> 10 developers.

### AI

> What type of development will they primarily perform?

### User

> Backend development. They will use Docker heavily.

### AI

> When do they need the laptops?

### User

> Before September 1.

### AI

> Based on the requirements, I recommend 32 GB RAM and 1 TB SSD. Would you like to continue with this specification?

### User

> Yes.

### AI

> I found 3 unused laptops and 2 laptops scheduled to become available before September 1.
>
> You requested 10 laptops, but 5 existing assets can partially satisfy the requirement. I recommend purchasing 5 new laptops.
>
> Would you like to proceed with 5 units?

### User

> Yes.

### AI

> Here is your Purchase Requisition draft.

```text
Purchase Requisition

Category:
IT Equipment

Item:
Laptop

Quantity:
5

Specification:
32 GB RAM
1 TB SSD

Purpose:
Backend Development

Required Date:
September 1, 2026

Justification:
New backend development team.

Demand Analysis:
10 units were initially requested.
5 existing/returning assets are available.
5 new units are therefore recommended.
```

### User

> Submit it.

The system submits the PR to the procurement system.

---

# 19. Future Enterprise Expansion

The current MVP is intentionally limited to the **Demand-to-PR** stage.

The broader Enterprise Procurement AI platform can later extend the workflow:

```text
                    Procurement Copilot
                         Orchestrator
                              │
                              ▼
                    Requirement & Demand
                              │
                              ▼
                             PR
                              │
                         PR Approval
                              │
                              ▼
                     Procurement Planner
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
       Vendor Discovery   RFQ / RFP       Existing Vendor
              │               │                │
              └───────────────┼────────────────┘
                              ▼
                     Vendor Comparison
                              │
                              ▼
                         Negotiation
                              │
                              ▼
                    Purchase Recommendation
                              │
                              ▼
                             PO
                              │
                              ▼
                       Goods / Service
                           Receipt
                              │
                              ▼
                          Invoice
                              │
                              ▼
                       Invoice Matching
                              │
                              ▼
                           Payment
                              │
                              ▼
                    Supplier Management
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
        Supplier Risk     Performance      Lifecycle
                              │
                              ▼
                         Analytics
```

This allows the current MVP to evolve into the broader **Enterprise Procurement AI Platform** without changing the fundamental architectural concept.

---

# 20. MVP Scope Summary

### In Scope

```text
Natural Language Request
        ↓
Requirement Clarification
        ↓
Requirement Extraction
        ↓
Requirement Validation
        ↓
Requirement Confirmation
        ↓
Demand Analysis
        ↓
Demand Recommendation
        ↓
User Confirmation
        ↓
PR Draft
        ↓
PR Submission
```

### Out of Scope

```text
Vendor Selection
Vendor Discovery
RFQ
RFP
Negotiation
Contract
Supplier Management
PO
Invoice
Payment
```

### Core Architecture

```text
1 Orchestrator
      │
      ├── Requirement Clarification Agent
      │       ├── Requirement Interview Skill
      │       ├── Requirement Extraction Skill
      │       ├── Requirement Validation Skill
      │       └── Requirement Summarization Skill
      │
      └── Demand Analysis Agent
              ├── Demand Assessment Skill
              ├── Demand Validation Skill
              ├── Demand Recommendation Skill
              └── Demand Explanation Skill

Tools:
- Category
- Specification
- Policy
- Inventory
- Asset
- Purchase History
- Open PR
- Open PO
- Usage/Demand
- Budget
```

**Core product principle:**

> **The user provides the business need. The LLM helps understand and reason about the need. Deterministic tools provide factual organizational data. The user remains in control of the final PR.**

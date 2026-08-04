# ProcureAI — Product Requirements Document

**Project type:** Portfolio project
**Domain:** Procurement / Purchasing automation
**Architecture pattern:** Supervisor/Orchestrator + specialized agents
**Tech stack:** LangGraph, FastAPI, PostgreSQL, React/Vite, Docker Compose

---

## 1. Executive Summary

ProcureAI is an agentic AI platform that automates the end-to-end procurement lifecycle — from Purchase Requisition (PR) through Purchase Order (PO), Goods Receipt (GR), and Invoice matching. It uses a supervisor/orchestrator pattern to coordinate four specialized agents, each responsible for a distinct stage of the procurement pipeline, with human-in-the-loop approval gates at key decision points.

The platform demonstrates agentic reasoning most heavily in its **Invoice Matching Agent**, which performs 3-way match reconciliation (PO vs GR vs Invoice) and autonomously flags discrepancies with explainable reasoning — the centerpiece of the portfolio's technical depth.

---

## 2. Problem Statement

Manual procurement processes are slow and error-prone:

- Purchase Requisitions are often incomplete or exceed budget without being caught early.
- Vendor selection and PO creation are manual, repetitive, and inconsistent.
- Goods Receipt confirmation is disconnected from the PO, causing over-receiving or missed deliveries.
- Invoice-to-PO-to-GR matching (3-way match) is typically done manually in spreadsheets or ERP screens, which is slow and misses subtle discrepancies (quantity mismatch, price variance, duplicate invoices, invoices without a corresponding GR).

These inefficiencies cause payment delays, budget leakage, and audit risk. ProcureAI addresses this by automating validation, matching, and discrepancy detection while keeping humans in control of approvals.

---

## 3. User Personas

| Persona | Role | Needs |
|---|---|---|
| **Requester** | Employee submitting a Purchase Request | Fast submission, clear status visibility, quick feedback on rejected/incomplete requests |
| **Procurement Officer** | Reviews PRs, manages vendor selection, issues POs | Efficient PR-to-PO conversion, vendor comparison support, reduced manual data entry |
| **Warehouse/Receiving Staff** | Confirms goods/services received | Simple GR entry against existing PO, mismatch alerts |
| **AP (Accounts Payable) Clerk** | Processes vendor invoices | Automated 3-way match, clear discrepancy explanations, faster invoice approval cycle |
| **Finance Manager / Approver** | Approves PRs/POs above threshold, resolves flagged discrepancies | Trustworthy AI reasoning, audit trail, ability to override agent decisions |

---

## 4. Scope

### In Scope
- End-to-end pipeline: PR → PO → GR → Invoice, covering all four stages.
- Orchestrator-driven state management of a procurement request through its lifecycle.
- Human-in-the-loop approval gates (PR→PO approval, and discrepancy resolution in invoice matching).
- Basic vendor data model with optional web-search-assisted pricing lookup when internal vendor/pricing data is unavailable.

### Out of Scope (v1)
- Full vendor onboarding/compliance workflows (KYC, contracts).
- Multi-currency and tax-engine integration.
- ERP system integration (SAP, Oracle) — data is self-contained in ProcureAI's own DB.
- Payment execution (AP clerk still processes payment outside the system).

---

## 5. System Architecture

### 5.1 Orchestrator (Supervisor Agent)
Coordinates the procurement request through its lifecycle, maintaining state (`PR ID → PO ID → GR ID(s) → Invoice ID(s)`), routing to the correct sub-agent based on current stage, and pausing for human approval at defined gates.

### 5.2 Sub-Agents

| Agent | Responsibility | Depth |
|---|---|---|
| **Requisition Agent** | Validates PR completeness (item, qty, budget code, justification), checks against budget/category rules, flags anomalies (e.g. price outliers vs. historical data) | Light — rule-based validation |
| **Sourcing & PO Agent** | Compares vendors/pricing (internal data if available, otherwise web-search-assisted lookup for reference pricing), generates PO from an approved PR | Moderate |
| **Goods Receipt Matching Agent** | Matches recorded GR against the originating PO (item, quantity), flags over/under-receipt | Light-moderate |
| **Invoice Matching Agent (3-way match)** | Reconciles Invoice vs. PO vs. GR; detects quantity mismatch, price variance, duplicate invoices, invoices without GR; produces explainable discrepancy reasoning | **Deep — primary showcase agent** |

### 5.3 Cross-Cutting Workflow Gates
- **PR → PO approval**: human approval required before PO issuance (configurable threshold).
- **Discrepancy resolution gate**: any 3-way match discrepancy is routed to a human approver rather than auto-resolved.

### 5.4 High-Level Flow Diagram (textual)

```
Requester submits PR
      │
      ▼
[Requisition Agent] ──validates──▶ (fail → return to requester)
      │ pass
      ▼
 Human Approval (PR)
      │ approved
      ▼
[Sourcing & PO Agent] ──generates──▶ PO issued
      │
      ▼
Receiving records delivery
      │
      ▼
[GR Matching Agent] ──matches──▶ (mismatch → flag)
      │ GR confirmed
      ▼
Vendor submits Invoice
      │
      ▼
[Invoice Matching Agent] ──3-way match──▶ (discrepancy → Human Approval gate)
      │ match clean
      ▼
Invoice approved for payment
```

---

## 6. Functional Requirements

### 6.1 Requisition Agent
- FR-1.1: Validate required fields (item description, quantity, unit, budget code, justification).
- FR-1.2: Check requested amount against available budget for the given code.
- FR-1.3: Flag price outliers by comparing against historical PR data (if available).
- FR-1.4: Return structured validation result (pass / fail + reasons) to the orchestrator.

### 6.2 Sourcing & PO Agent
- FR-2.1: Retrieve internal vendor/pricing data for the requested item category, if available.
- FR-2.2: If no internal data exists, perform a web search to find reference market pricing and present it as a suggestion (clearly labeled as external/unverified data).
- FR-2.3: Present top vendor candidates (or reference pricing) for Procurement Officer selection.
- FR-2.4: Generate a PO document from the approved PR and selected vendor, with line items, quantities, and agreed price.

### 6.3 Goods Receipt Matching Agent
- FR-3.1: Accept GR entries against a specific PO.
- FR-3.2: Match received item/quantity against PO line items.
- FR-3.3: Flag over-receipt, under-receipt, or item mismatch.
- FR-3.4: Support partial/multiple GRs against a single PO.

### 6.4 Invoice Matching Agent (3-way match) — Primary Depth Area
- FR-4.1: Parse invoice data (item, quantity, unit price, total) — manual entry or structured upload for v1.
- FR-4.2: Match invoice against corresponding PO (price and quantity).
- FR-4.3: Match invoice against corresponding GR (quantity actually received).
- FR-4.4: Detect and classify discrepancy types: price variance (with % threshold), quantity mismatch, invoice without GR, duplicate invoice submission.
- FR-4.5: Generate a human-readable explanation of each discrepancy (what mismatched, expected vs. actual values, confidence level).
- FR-4.6: Route discrepancies above a configurable severity threshold to a human approver; auto-approve clean matches.
- FR-4.7: Maintain a full audit trail of the matching decision and any human override.

---

## 7. High-Level Data Model

**Core entities:**
- `PurchaseRequisition` (PR): id, requester, items[], budget_code, status, created_at
- `Vendor`: id, name, category, contact_info, historical_pricing[] (optional)
- `PurchaseOrder` (PO): id, pr_id, vendor_id, line_items[], total_amount, status
- `GoodsReceipt` (GR): id, po_id, received_items[], received_at, status
- `Invoice`: id, po_id, gr_id(s), line_items[], total_amount, status
- `MatchResult`: id, invoice_id, discrepancies[], resolution_status, resolved_by

---

## 8. Tech Stack

- **Orchestration:** LangGraph (state machine for PR→PO→GR→Invoice lifecycle)
- **Backend:** FastAPI, SQLAlchemy (async), Alembic
- **Database:** PostgreSQL
- **Frontend:** React + Vite, Recharts (for procurement metrics dashboard)
- **Package management:** `uv`
- **Containerization:** Docker Compose
- **External data:** Web search tool (for Sourcing Agent reference pricing fallback)

---

## 9. Success Metrics

- **Cycle time reduction:** average PR-to-PO time reduced vs. manual baseline (simulated).
- **Match accuracy:** % of invoices correctly auto-matched without human correction.
- **Discrepancy detection rate:** % of injected/synthetic discrepancies correctly caught by the Invoice Matching Agent.
- **False positive rate:** % of clean invoices incorrectly flagged.
- **Explainability quality:** qualitative — discrepancy explanations are clear enough for an AP clerk to act on without re-investigating manually.

---

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Web-search-based pricing data is unreliable/unverifiable | Clearly label as "external reference, unverified" and never auto-approve POs based solely on it |
| 3-way match logic produces false positives, eroding trust | Tune thresholds using synthetic test data; always allow human override with reasoning captured |
| Scope creep toward full ERP-like functionality | Explicitly keep PO/payment execution and ERP integration out of v1 scope |
| LangGraph state complexity across 4 agents + gates | Design state schema early (next step: technical design doc) before implementation |

---

## 11. Open Questions

1. Should invoice data be entered manually (form) or via document upload (would require OCR/parsing — out of scope for v1 unless prioritized)?
2. What discrepancy severity thresholds (e.g., price variance %) should trigger human review vs. auto-approval?
3. Should vendor historical pricing be seeded with mock data, or left empty to force the web-search fallback path (better showcases that capability)?

---

## 12. Next Steps

The next deliverable is a **Technical Design Document** covering the PostgreSQL schema, API contracts (FastAPI endpoints per agent/stage), and LangGraph state graph design for the orchestrator.
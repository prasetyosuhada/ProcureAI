# ProcureAI — REST API & Event Stream Specification

**Document Version:** 1.0.0  
**Base URL:** `/api/v1`  
**Protocol:** HTTP/2 & Server-Sent Events (SSE)  
**Auth Scheme:** Bearer Token (JWT)

---

## 1. Global API Conventions

### 1.1 Content Types & Headers
* Request bodies must use `Content-Type: application/json`.
* Real-time workflow state updates use `Accept: text/event-stream`.
* Authenticated requests must include `Authorization: Bearer <jwt_token>`.

### 1.2 Standard Error Response Schema (RFC 7807)
All 4xx and 5xx errors return a uniform structured error payload:

```json
{
  "type": "https://api.procureai.dev/errors/DISCREPANCY_NOT_RESOLVED",
  "title": "Unresolved Discrepancy",
  "status": 400,
  "detail": "Invoice INV-99231 has unhandled price variance discrepancies and requires human override before approval.",
  "instance": "/api/v1/invoices/b3c7.../approve",
  "code": "ERR_UNRESOLVED_DISCREPANCY",
  "timestamp": "2026-08-03T23:15:00Z"
}
```

---

## 2. API Endpoint Matrix

| Module | Method | Endpoint | Role Allowed | Description |
|---|---|---|---|---|
| **Auth** | `POST` | `/api/v1/auth/login` | Public | Authenticate user & receive JWT |
| | `GET` | `/api/v1/auth/me` | Authenticated | Get current user profile & role |
| **Requisitions** | `POST` | `/api/v1/requisitions` | `REQUESTER` | Submit PR & trigger Requisition Agent |
| | `GET` | `/api/v1/requisitions` | All Roles | List PRs with filters |
| | `GET` | `/api/v1/requisitions/{id}` | All Roles | Get PR details & validation results |
| **Sourcing & PO** | `POST` | `/api/v1/purchase-orders/from-pr/{pr_id}` | `PROCUREMENT_OFFICER` | Generate PO & run Sourcing Agent |
| | `GET` | `/api/v1/purchase-orders` | All Roles | List issued POs |
| | `GET` | `/api/v1/purchase-orders/{id}` | All Roles | Get PO details & line items |
| **Goods Receipt** | `POST` | `/api/v1/goods-receipts` | `WAREHOUSE_STAFF` | Record Goods Receipt against a PO |
| | `GET` | `/api/v1/goods-receipts/po/{po_id}` | All Roles | List all GRs for a specific PO |
| **Invoice & Matching**| `POST` | `/api/v1/invoices` | `AP_CLERK` | Submit invoice & trigger 3-Way Match |
| | `GET` | `/api/v1/invoices/{id}` | All Roles | Get Invoice details |
| | `GET` | `/api/v1/invoices/{id}/match-result`| All Roles | Get 3-Way Match evaluation & reasoning |
| **HITL Approvals** | `GET` | `/api/v1/approvals/pending` | `FINANCE_MANAGER`, `PROCUREMENT_OFFICER` | List items waiting for human gate action |
| | `POST` | `/api/v1/approvals/pr/{pr_id}` | `FINANCE_MANAGER`, `PROCUREMENT_OFFICER` | Approve or Reject PR |
| | `POST` | `/api/v1/approvals/discrepancy/{invoice_id}` | `FINANCE_MANAGER` | Resolve/Override Invoice 3-Way discrepancy |
| **Real-Time Engine** | `GET` | `/api/v1/workflows/{pr_id}/stream` | All Roles | SSE stream of LangGraph agent state transitions |

---

## 3. Endpoint Specifications & Payload Examples

### 3.1 Submit Purchase Requisition (PR)
**`POST /api/v1/requisitions`**

* **Description:** Submits a new PR and immediately executes the **Requisition Agent** to validate items, check budget, and detect price outliers.

#### Request Payload:
```json
{
  "budget_id": "c7a812ef-7231-4c12-9842-120092348512",
  "justification": "Upgrade engineering team workstations for AI model training",
  "line_items": [
    {
      "item_name": "NVIDIA RTX 4090 GPU 24GB",
      "category": "Hardware",
      "quantity": 2,
      "estimated_unit_price": 1600.00
    },
    {
      "item_name": "DDR5 RAM 64GB Kit",
      "category": "Hardware",
      "quantity": 4,
      "estimated_unit_price": 210.00
    }
  ]
}
```

#### Response (201 Created):
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "pr_number": "PR-2026-0089",
  "status": "APPROVAL_PENDING",
  "total_amount": 4040.00,
  "validation_result": {
    "is_valid": true,
    "budget_check": {
      "status": "SUFFICIENT",
      "allocated": 50000.00,
      "remaining_after_pr": 32400.00
    },
    "anomalies_detected": [
      {
        "item_name": "NVIDIA RTX 4090 GPU 24GB",
        "flag_type": "PRICE_OUTLIER_WARNING",
        "severity": "LOW",
        "message": "Unit price $1,600.00 is 5% below historical average ($1,685.00)."
      }
    ]
  },
  "created_at": "2026-08-03T23:16:00Z"
}
```

---

### 3.2 Submit Invoice & Run 3-Way Match
**`POST /api/v1/invoices`**

* **Description:** Registers a vendor invoice and triggers the **Invoice Matching Agent** to perform a 3-way match against the linked PO and associated GRs.

#### Request Payload:
```json
{
  "invoice_number": "INV-2026-9912",
  "po_id": "d9b23e12-8812-4211-9011-445566778899",
  "vendor_id": "v1123456-7890-abcd-ef01-234567890abc",
  "invoice_date": "2026-08-02",
  "total_amount": 4240.00,
  "tax_amount": 0.00,
  "line_items": [
    {
      "description": "NVIDIA RTX 4090 GPU 24GB",
      "quantity": 2,
      "unit_price": 1700.00,
      "total": 3400.00
    },
    {
      "description": "DDR5 RAM 64GB Kit",
      "quantity": 4,
      "unit_price": 210.00,
      "total": 840.00
    }
  ]
}
```

#### Response (200 OK — Discrepancy Detected):
```json
{
  "id": "e8123901-1122-3344-5566-778899aabbcc",
  "invoice_number": "INV-2026-9912",
  "status": "DISCREPANCY_FLAGGED",
  "total_amount": 4240.00,
  "match_result": {
    "overall_status": "DISCREPANCY_DETECTED",
    "confidence_score": 0.991,
    "discrepancies": [
      {
        "type": "PRICE_VARIANCE",
        "severity": "HIGH",
        "field": "unit_price",
        "item_name": "NVIDIA RTX 4090 GPU 24GB",
        "expected_value": 1600.00,
        "actual_value": 1700.00,
        "variance_percentage": 6.25,
        "explanation": "Invoiced unit price ($1,700.00) exceeds agreed PO price ($1,600.00) by +6.25%, exceeding allowed threshold of 2.00%."
      }
    ],
    "reasoning_summary": "Invoice INV-2026-9912 flagged due to 1 high-severity Price Variance discrepancy on Line #1. Total billed ($4,240.00) exceeds PO total ($4,040.00) by $200.00. Automatic approval blocked; routed to Finance Manager for review.",
    "requires_human_override": true
  }
}
```

---

### 3.3 Human Discrepancy Resolution Gate
**`POST /api/v1/approvals/discrepancy/{invoice_id}`**

* **Description:** Allows a Finance Manager to resolve or override an invoice discrepancy flagged by the 3-Way Match Agent.

#### Request Payload:
```json
{
  "action": "FORCE_APPROVE",
  "reason": "Vendor updated price due to verified tariff increase; approved by Procurement VP.",
  "adjusted_total_amount": 4240.00
}
```

#### Response (200 OK):
```json
{
  "invoice_id": "e8123901-1122-3344-5566-778899aabbcc",
  "previous_status": "DISCREPANCY_FLAGGED",
  "new_status": "APPROVED_FOR_PAYMENT",
  "resolution_summary": {
    "action": "FORCE_APPROVE",
    "resolved_by": "Finance Manager (user_id: 11223344-5566...)",
    "timestamp": "2026-08-03T23:18:22Z",
    "override_note": "Vendor updated price due to verified tariff increase; approved by Procurement VP."
  }
}
```

---

### 3.4 Server-Sent Events (SSE) Real-Time Agent Workflow Stream
**`GET /api/v1/workflows/{pr_id}/stream`**

* **Description:** Streams live execution state of the LangGraph Supervisor & Sub-Agents as nodes execute.

#### Event Stream Format:
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

event: node_start
data: {"node": "RequisitionValidationAgent", "timestamp": "2026-08-03T23:19:01Z"}

event: reasoning_step
data: {"agent": "RequisitionValidationAgent", "thought": "Checking budget code BG-IT-2026 remaining balance vs requested $4,040.00..."}

event: node_complete
data: {"node": "RequisitionValidationAgent", "status": "PASS", "result": {"is_valid": true}}

event: interrupt_triggered
data: {"gate": "PR_APPROVAL_PENDING", "assigned_role": "FINANCE_MANAGER", "message": "Graph paused waiting for human manager approval."}
```

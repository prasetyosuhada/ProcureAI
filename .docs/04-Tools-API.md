# Tools & API Integration Specification

# ProcureAI

**Document Status:** Draft
**Version:** 1.0
**Related Documents:** [01-PRD.md](01-PRD.md), [03-Agent-Design.md](03-Agent-Design.md)

---

## 1. Overview

This document specifies the interfaces (API Contracts) for the deterministic tools that the Agentic AI uses to interact with enterprise data. 

The AI Agents (LangChain/Gemini) will be provided with these function schemas. When an agent decides to use a tool, LangChain will execute the corresponding Python function, which will in turn call the internal FastAPI endpoints or external ERP systems.

---

## 2. Authentication & Context

Agents do not handle raw authentication tokens. FastAPI handles user authentication and injects a `UserContext` object into every tool call to ensure data access is restricted to what the user is authorized to see (e.g., checking budgets only for their department).

**Implicit Parameters (Injected by Backend, hidden from LLM):**
*   `user_id`: ID of the requester.
*   `department_id`: Department of the requester.
*   `cost_center`: Cost center code.

---

## 3. Requirement Clarification Tools

These tools are primarily used by the **Requirement Clarification Agent** to standardize user requests.

### 3.1 `get_categories(query: str)`
Looks up standard procurement categories based on a natural language query.
*   **Input:** `query` (string) - The item the user is asking for (e.g., "laptop").
*   **Output:** List of matching categories.
*   **Example Response:**
    ```json
    {
      "status": "success",
      "data": [
        {"category_id": "IT-HW-01", "category_name": "IT Equipment > Laptops"},
        {"category_id": "IT-HW-02", "category_name": "IT Equipment > Desktops"}
      ]
    }
    ```

### 3.2 `get_specifications(category_id: str, item_name: str)`
Retrieves company-approved standard specifications for a given item.
*   **Input:** `category_id` (string), `item_name` (string).
*   **Output:** Dictionary of standard specs.
*   **Example Response:**
    ```json
    {
      "standard_models": [
        {
          "model": "Standard Developer Laptop",
          "specs": {"ram": "32GB", "storage": "1TB SSD", "os": "macOS/Windows"}
        },
        {
          "model": "Standard Business Laptop",
          "specs": {"ram": "16GB", "storage": "512GB SSD", "os": "Windows"}
        }
      ]
    }
    ```

### 3.3 `get_procurement_policy(item_name: str, estimated_value: float = None)`
Retrieves policies relevant to the item or value.
*   **Input:** `item_name` (string), optional `estimated_value` (float).
*   **Output:** Text string explaining the policy.
*   **Example Response:**
    ```json
    {
      "policy_text": "All IT hardware requests must be approved by the IT Manager. Laptops require a minimum specification of 16GB RAM for security software."
    }
    ```

---

## 4. Demand Analysis Tools

These tools are used by the **Demand Analysis Agent** to assess if a requested purchase is justified based on existing organizational assets and history.

### 4.1 `get_inventory(item_name: str, category_id: str)`
Checks current warehouse/IT stock for unused items.
*   **Input:** `item_name` (string), `category_id` (string).
*   **Output:** Quantity of available unused stock.
*   **Example Response:**
    ```json
    {
      "item": "Laptop",
      "available_quantity": 3,
      "location": "IT Store Room A"
    }
    ```

### 4.2 `get_assets(item_name: str)`
Checks for existing organizational assets that are either unused or scheduled to be returned soon (e.g., from offboarding employees).
*   **Input:** `item_name` (string).
*   **Output:** Count of assets becoming available.
*   **Example Response:**
    ```json
    {
      "currently_unused": 0,
      "scheduled_returns_next_30_days": 2,
      "total_available_soon": 2
    }
    ```

### 4.3 `get_open_prs_and_pos(item_name: str, department_id: str)`
Checks if someone else in the department has already requested or ordered this item recently to prevent duplicate orders.
*   **Input:** `item_name` (string). *(`department_id` injected implicitly)*
*   **Output:** Summary of open PRs/POs.
*   **Example Response:**
    ```json
    {
      "open_prs": [{"pr_id": "PR-992", "quantity": 5, "status": "Pending Approval"}],
      "open_pos": [],
      "total_in_pipeline": 5
    }
    ```

### 4.4 `get_purchase_history(item_name: str, department_id: str)`
Retrieves historical data to help the AI understand typical consumption patterns.
*   **Input:** `item_name` (string).
*   **Output:** Historical purchase frequency and quantities over the last 12 months.
*   **Example Response:**
    ```json
    {
      "last_12_months_total": 20,
      "average_order_quantity": 5,
      "last_order_date": "2026-03-15"
    }
    ```

### 4.5 `get_budget_status(cost_center: str, category_id: str)`
Retrieves remaining budget for the category. (Note: AI does not enforce budget rules, but uses this as context for recommendations).
*   **Input:** `category_id` (string). *(`cost_center` injected implicitly)*
*   **Output:** Budget utilization status.
*   **Example Response:**
    ```json
    {
      "cost_center": "ENG-001",
      "allocated_budget": 50000.00,
      "consumed_budget": 35000.00,
      "remaining_budget": 15000.00,
      "currency": "USD"
    }
    ```

---

## 5. Tool Error Handling

If a tool encounters an error (e.g., API timeout or connection failure to the ERP), it must return a structured error message to the LLM rather than crashing the system.

**Example Error Response:**
```json
{
  "status": "error",
  "message": "Inventory system is currently unreachable. Please inform the user that inventory checks are temporarily unavailable."
}
```
The LLM is instructed to handle this gracefully in its natural language response to the user.

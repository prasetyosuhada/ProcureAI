# AI Evaluation & Test Plan

# ProcureAI

**Document Status:** Draft
**Version:** 1.0
**Related Documents:** [01-PRD.md](01-PRD.md), [03-Agent-Design.md](03-Agent-Design.md), [04-Tools-API.md](04-Tools-API.md)

---

## 1. Overview

Testing an Agentic AI system like the ProcureAI requires a different approach compared to traditional software testing. Because Large Language Models (LLMs) produce non-deterministic text, traditional assertion-based unit tests are insufficient. 

This document outlines the strategy for evaluating the AI agents, ensuring they meet the product requirements without hallucinating data, violating security boundaries, or making unauthorized decisions.

---

## 2. Evaluation Methodology

We will employ a three-tiered testing strategy:

1.  **Unit Tests (Deterministic):** Standard `pytest` tests to ensure FastAPI endpoints work, LangGraph state transitions occur as expected, and tool wrappers correctly handle API responses.
2.  **LLM-as-a-Judge (Automated E2E):** Using a stronger LLM (e.g., Gemini 1.5 Pro) to evaluate the outputs of the Copilot's agents against a set of predefined rubrics.
3.  **Human Evaluation (UAT):** Procurement experts and internal employees testing the conversational UI to assess tone, UX, and accuracy.

---

## 3. Test Scenarios (Golden Dataset)

A "Golden Dataset" of test cases must be created. Below are the key scenarios that must be evaluated continuously in CI/CD.

### Scenario 1: The Happy Path
*   **User Input:** "I need 2 standard developer laptops for new hires starting next week."
*   **Expected Agent Behavior:** 
    *   Agent recognizes all required fields (Item, Quantity, Purpose, Date) are almost complete.
    *   Agent may ask only 1 quick confirmation question.
    *   Demand Agent runs `get_assets` and calculates the recommendation.

### Scenario 2: Ambiguous / Incomplete Request
*   **User Input:** "We need new monitors for the design team."
*   **Expected Agent Behavior:** 
    *   Agent detects missing Quantity, Size/Spec, and Required Date.
    *   Agent asks ONE specific clarification question at a time (e.g., "How many monitors do you need?").
    *   **Failure Condition:** Agent assumes a quantity or specification without asking.

### Scenario 3: Demand Analysis & Inventory Override
*   **User Input:** "I need 10 ergonomic chairs."
*   **Mock Tool Data:** `get_inventory` returns 4 chairs available.
*   **Expected Agent Behavior:** 
    *   Agent recommends purchasing exactly **6** new chairs.
    *   Agent provides clear justification explaining the 4 available chairs.
    *   **Failure Condition:** Agent recommends 10 chairs despite inventory, or calculates the math wrong.

### Scenario 4: Out-of-Scope / Vendor Sourcing (Guardrail Test)
*   **User Input:** "I need 5 laptops. Can you compare prices between Dell and Lenovo and buy the cheapest one?"
*   **Expected Agent Behavior:** 
    *   Agent politely refuses the vendor comparison task.
    *   Agent redirects the user to clarify the technical specifications needed, stating that sourcing is handled separately by the procurement team.

### Scenario 5: Policy Violation Handling
*   **User Input:** "I want to buy a $5000 gaming laptop for data entry."
*   **Mock Tool Data:** `get_procurement_policy` states maximum budget for data entry laptops is $1000.
*   **Expected Agent Behavior:** 
    *   Agent informs the user of the policy restriction.
    *   Agent suggests an alternative specification that complies with the policy.

---

## 4. Key Performance Indicators (KPIs) & Metrics

When running automated LLM evaluations, we will score the system against these metrics:

| Metric | Description | Target / Threshold |
| :--- | :--- | :--- |
| **Requirement Extraction Accuracy** | Percentage of times the `requirementDraft` JSON accurately matches the user's intent. | > 95% |
| **Tool Invocation Accuracy** | Percentage of times the agent calls the *correct* tool with the *correct* parameters. | > 98% |
| **Hallucination Rate** | Percentage of responses where the agent invents data (e.g., faking inventory numbers). | 0% (Zero Tolerance) |
| **Clarification Efficiency** | Average number of chat turns required to reach a complete `requirementDraft`. | < 4 turns |
| **Math Accuracy (Demand)** | Percentage of times the Demand Agent correctly subtracts available assets from requested quantity. | 100% |

---

## 5. Implementation of Automated Testing

We will implement automated testing using **LangSmith** (or a similar LLM evaluation framework).

1.  **Mocking Tools:** During automated testing, all enterprise API tools will be mocked to return deterministic JSON responses.
2.  **State Inspection:** Tests will assert not just the final text output, but the internal LangGraph state (e.g., `assert state["requirementDraft"]["quantity"] == 10`).
3.  **Rubric Evaluation:** For conversational output, an LLM evaluator will be prompted with: *"Did the ProcureAI remain polite? Did it ask only one question? Output YES or NO."*

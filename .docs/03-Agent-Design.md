# Agent & Prompt Design Document

# ProcureAI

**Document Status:** Draft
**Version:** 1.0
**Related Documents:** [01-PRD.md](01-PRD.md), [02-System-Architecture.md](02-System-Architecture.md)

---

## 1. Overview

This document defines the behavioral instructions (System Prompts), expected data structures (JSON Schemas), and state management design for the AI Agents within the Procurement Copilot. 

Since the system uses LangGraph, the agents are not fully autonomous general-purpose AI; they are bounded components within a state machine, each with specific skills and responsibilities.

---

## 2. Global Guardrails (For All Agents)

The following rules apply to all Language Model interactions within the system:
1.  **No Hallucination of Data:** Agents must NEVER invent inventory numbers, budget figures, asset availability, or organizational policies. This data must ONLY come from external tools.
2.  **No Vendor Recommendations:** The scope of this MVP is limited to PR creation. Agents must actively refuse to perform vendor sourcing, comparison, or price negotiation.
3.  **Human in the Loop:** Agents cannot unilaterally submit a PR. They must present a draft and wait for user confirmation.
4.  **Tone & Persona:** Agents must be professional, concise, helpful, and speak in the context of an internal enterprise assistant.

---

## 3. LangGraph Global State Schema

To pass context between agents, a shared graph state is maintained.

```typescript
type GraphState = {
    // Standard chat history
    messages: BaseMessage[]; 
    
    // User context injected by FastAPI
    userContext: {
        userId: string;
        department: string;
        costCenter: string;
    };
    
    // Extracted structured requirement
    requirementDraft: {
        category?: string;
        item?: string;
        quantity?: number;
        purpose?: string;
        required_date?: string;
        specifications?: Record<string, string>;
        isComplete: boolean;
    };
    
    // Analysis and Recommendation
    demandAnalysis: {
        availableAssets: number;
        recommendedQuantity?: number;
        justification?: string;
        isComplete: boolean;
    };
    
    // Routing flag used by Orchestrator
    nextAgent: "Clarification" | "Demand" | "GeneratePR" | "End";
}
```

---

## 4. Requirement Clarification Agent

### 4.1 Purpose
To transform an ambiguous natural-language purchasing request into a complete, structured requirement array. It determines what information is missing and asks contextual questions.

### 4.2 System Prompt Design
```text
You are the Requirement Clarification Agent for the ProcureAI. 
Your goal is to understand what the user wants to purchase and extract the necessary details to form a complete Purchase Requisition.

Available Tools:
- CategoryTool: To lookup standard procurement categories.
- SpecificationTool: To find company-standard specifications for requested items.

Instructions:
1. Review the conversation history and the current `requirementDraft`.
2. Determine if the request contains all mandatory fields: Item, Quantity, Purpose, Required Date, and Specifications.
3. If mandatory information is missing, formulate ONE concise clarification question to ask the user. Do not ask for everything at once.
4. If the user provides information, extract it and update the `requirementDraft` JSON structure.
5. If the user mentions a specific brand or specification, use the `SpecificationTool` to check if it aligns with company standards.
6. Once all fields are populated and validated, set `isComplete` to true.

Constraints:
- Do not ask about budget or existing inventory; that will be handled later.
- Keep questions short and conversational.
```

### 4.3 Output Schema (Structured Extraction)
When extracting data from the conversation, the agent outputs this JSON:
```json
{
  "category": "IT Equipment",
  "item": "Laptop",
  "quantity": 10,
  "purpose": "New Backend Development Team",
  "required_date": "2026-09-01",
  "specifications": {
    "ram": "32GB",
    "storage": "1TB SSD",
    "workload": "Docker/Backend"
  },
  "isComplete": true
}
```

---

## 5. Demand Analysis Agent

### 5.1 Purpose
To analyze the requested demand (from the Clarification Agent) against actual organizational data and recommend an optimal purchase quantity.

### 5.2 System Prompt Design
```text
You are the Demand Analysis Agent. The user has finalized their purchase requirement.
Your job is to determine if the requested quantity is reasonable and provide a data-backed recommendation.

Available Tools:
- InventoryTool: Get current stock of the requested item.
- AssetTool: Get existing unused or soon-to-return assets.
- PurchaseHistoryTool: Review past purchases for this item.
- UsageTool: Check historical consumption.

Instructions:
1. Review the user's requested `item` and `quantity`.
2. You MUST call the `InventoryTool` and `AssetTool` to find existing resources that can fulfill this request.
3. Calculate the recommended purchase quantity using this formula: 
   Recommended Quantity = Requested Quantity - (Available Inventory + Available Assets).
   Note: Recommended Quantity cannot be less than 0.
4. Provide a clear, natural-language explanation of how you arrived at this recommendation.
5. Ask the user if they agree with the recommended quantity to proceed with the PR draft.

Constraints:
- Do NOT guess inventory numbers. You must use the tools.
- Do NOT alter the item specifications, only analyze the quantity.
```

### 5.3 Output Schema (Recommendation)
```json
{
  "availableAssets": 5,
  "recommendedQuantity": 5,
  "justification": "You requested 10 laptops. We found 3 unused laptops in IT stock and 2 scheduled to be returned next week. Therefore, we recommend purchasing 5 new units to meet your requirement.",
  "isComplete": true
}
```

---

## 6. PR Generation (Final Step)

The final step is not an autonomous agent but a simple deterministic template generation step within the LangGraph Orchestrator. It combines the `requirementDraft` and `demandAnalysis` state objects into a structured PR JSON to be sent to the React UI for final user review.

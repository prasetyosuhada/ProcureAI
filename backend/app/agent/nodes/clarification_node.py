import re
import logging
from typing import Dict, Any, List, Sequence
from langchain_core.messages import AIMessage, SystemMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.agent.state import (
    GraphState,
    RequirementDraftSchema,
    PRSpecification,
    PRArtifact,
    AgentAction,
    AttentionItem,
)
from app.agent.prompts import REQUIREMENT_CLARIFICATION_PROMPT
from app.agent.activity import emit_activity, run_with_activity
from app.tools.clarification_tools import get_categories, get_specifications, get_procurement_policy
from app.core.config import settings

logger = logging.getLogger(__name__)

CLARIFICATION_TOOLS = [get_categories, get_specifications, get_procurement_policy]


# ==============================================================================
# Helpers
# ==============================================================================

def extract_text_from_content(content: Any) -> str:
    """Safely extracts clean plain text from LangChain message content."""
    if isinstance(content, str):
        return content.strip()
    elif isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if "text" in block:
                    parts.append(str(block["text"]))
                elif "content" in block:
                    parts.append(str(block["content"]))
            elif hasattr(block, "text"):
                parts.append(str(block.text))
        return "\n".join(parts).strip()
    elif isinstance(content, dict):
        if "text" in content:
            return str(content["text"]).strip()
        elif "content" in content:
            return str(content["content"]).strip()
    return str(content).strip()


def get_last_user_message(messages: Sequence[BaseMessage]) -> str:
    """Extract the text content of the latest human message from conversation history."""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            return extract_text_from_content(msg.content)
        elif hasattr(msg, "content") and not getattr(msg, "role", None) == "assistant":
            return extract_text_from_content(msg.content)
    return ""


def extract_requirement_heuristics(
    user_text: str,
    current_draft: Dict[str, Any],
    resolve_category: bool = True,
) -> Dict[str, Any]:
    """
    Dynamic rule-based fallback extractor for any item request (IT, furniture, software, supplies).
    Used during offline tests or when LLM API key is unavailable.
    """
    draft = RequirementDraftSchema().model_dump()
    if current_draft:
        draft.update(current_draft)

    specs = dict(draft.get("specifications") or {})
    text = user_text.strip()
    text_lower = text.lower()

    # 1. Dynamic Item & Category Extraction
    if not draft.get("item"):
        if "laptop" in text_lower or "macbook" in text_lower or "notebook" in text_lower:
            draft["item"] = "Laptop"
        elif "monitor" in text_lower or "screen" in text_lower or "display" in text_lower:
            draft["item"] = "Monitor"
        elif "chair" in text_lower or "seating" in text_lower:
            draft["item"] = "Ergonomic Chair"
        elif "desk" in text_lower or "table" in text_lower:
            draft["item"] = "Standing Desk"
        else:
            item_match = re.search(
                r'\b(?:need|want|buy|request|order|purchasing|for)\s+(?:to\s+buy\s+)?(?:a|an|\$[\d,]+|\d+)?\s*(?:a|an|\$[\d,]+|\d+)?\s*([a-zA-Z0-9\s\-/]{2,35}?)(?=\s+(?:for|before|by|with|to|in|\.)|\b|[.,;]|$)',
                text, re.IGNORECASE
            )
            if item_match:
                candidate = item_match.group(1).strip()
                candidate = re.sub(r'^(?:\$?\d+[\w,]*\s*)+', '', candidate).strip()
                candidate = re.sub(r'^(?:new|standard|high-end|refurbished|commercial)\s+', '', candidate, flags=re.IGNORECASE).strip()
                if candidate and len(candidate) > 1 and candidate.lower() not in ["the", "a", "an", "some", "these", "those"]:
                    item_title = candidate.title()
                    if item_title.endswith("s") and not item_title.endswith("ss"):
                        item_title = item_title[:-1]
                    draft["item"] = item_title

    if resolve_category and draft.get("item") and not draft.get("category"):
        cat_results = get_categories.invoke({"query": draft["item"]})
        if cat_results:
            draft["category"] = cat_results[0]["category_name"]

    # 2. Extract Quantity
    qty_match = re.search(r'\b(\d+)\s*(?:units?|pcs?|items?|laptops?|monitors?|chairs?|desks?|licenses?|devs?|developers?|members?)\b', text_lower)
    if not qty_match:
        qty_match = re.search(r'\b(?:for|need|want|buy|order)\s+(\d+)\b', text_lower)
    if qty_match:
        try:
            draft["quantity"] = int(qty_match.group(1))
        except ValueError:
            pass

    # 3. Extract Purpose
    if "backend" in text_lower:
        draft["purpose"] = "Backend Development Team"
        specs["workload"] = "Backend / Docker"
    elif "frontend" in text_lower:
        draft["purpose"] = "Frontend Development Team"
        specs["workload"] = "Frontend Web"
    elif "design" in text_lower or "ui/ux" in text_lower:
        draft["purpose"] = "UI/UX Design Team"
        specs["workload"] = "Graphic Design"
    elif "marketing" in text_lower:
        draft["purpose"] = "Marketing Department"
    elif not draft.get("purpose"):
        purpose_match = re.search(r'\bfor\s+([a-zA-Z0-9\s\-]{3,30}?)(?=\s+(?:before|by|with|in)\b|$)', text, re.IGNORECASE)
        if purpose_match:
            draft["purpose"] = purpose_match.group(1).strip().title()
        elif len(text) > 15:
            draft["purpose"] = text

    # 4. Extract Specifications
    ram_match = re.search(r'\b(\d+\s*gb)\s*ram\b', text_lower)
    if ram_match:
        specs["ram"] = ram_match.group(1).upper().replace(" ", "")
    elif "32gb" in text_lower or "32 gb" in text_lower:
        specs["ram"] = "32GB"
    elif "16gb" in text_lower or "16 gb" in text_lower:
        specs["ram"] = "16GB"

    storage_match = re.search(r'\b(\d+\s*(?:tb|gb))\s*(?:ssd|storage)\b', text_lower)
    if storage_match:
        val = storage_match.group(1).upper().replace(" ", "")
        specs["storage"] = f"{val} SSD" if not val.endswith("SSD") else val
    elif "1tb" in text_lower or "1 tb" in text_lower:
        specs["storage"] = "1TB SSD"
    elif "512gb" in text_lower or "512 gb" in text_lower:
        specs["storage"] = "512GB SSD"

    # GPU
    gpu_match = re.search(r'\b(rtx\s*\d{4}[a-zA-Z0-9\s]*|gtx\s*\d{4}[a-zA-Z0-9\s]*|apple\s*m\d\s*max|apple\s*m\d\s*pro)\b', text_lower)
    if gpu_match:
        specs["gpu"] = gpu_match.group(1).upper().strip()

    # 5. Extract Required Date
    if "sept" in text_lower or "september" in text_lower:
        draft["required_date"] = "2026-09-01"
    elif "next month" in text_lower or "next week" in text_lower:
        draft["required_date"] = "2026-09-01"
    else:
        date_match = re.search(r'\b(?:before|by|on|date)\s+([a-zA-Z]+\s+\d{1,2}|\d{4}-\d{2}-\d{2})\b', text_lower)
        if date_match:
            draft["required_date"] = date_match.group(1).title()

    draft["specifications"] = specs

    # 6. Evaluate Completeness
    is_complete = bool(
        draft.get("item") and
        draft.get("quantity") is not None and draft.get("quantity", 0) > 0 and
        draft.get("purpose") and
        draft.get("required_date")
    )
    draft["is_complete"] = is_complete

    return draft


def _build_pr_artifact_from_draft(
    draft: Dict[str, Any],
    user_context: Dict[str, Any],
    is_user_confirmed: bool
) -> Dict[str, Any]:
    """
    Converts legacy requirement_draft dict into Phase 1 PRArtifact format.
    Specification fields: is_confirmed is set to True ONLY via explicit action (Jalur 1)
    when is_user_confirmed is True (state['confirmation_action'] is True) and draft is complete.
    """
    raw_specs = draft.get("specifications", {})
    pr_specs: List[PRSpecification] = []

    for field_name, value in raw_specs.items():
        if value:
            pr_specs.append(PRSpecification(
                field_name=field_name,
                value=str(value),
                is_confirmed=is_user_confirmed and bool(draft.get("is_complete"))
            ))

    artifact = PRArtifact(
        item_name=draft.get("item"),
        category=draft.get("category"),
        quantity=draft.get("quantity"),
        department=user_context.get("department_id"),
        cost_center=user_context.get("cost_center"),
        purpose=draft.get("purpose"),
        required_date=draft.get("required_date"),
        specifications=pr_specs,
        status="draft",
        is_ready_for_confirmation=bool(draft.get("is_complete"))
    )
    return artifact.model_dump()


def _build_clarification_attention_items(
    draft: Dict[str, Any],
    user_context: Dict[str, Any],
    policy_result: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """
    Generates AttentionItem list based on specification and policy checks.
    IDs are deterministic: spec_{field_name}, policy_{rule_key}.
    """
    items: List[Dict[str, Any]] = []
    specs = draft.get("specifications", {})

    # Check IT policy compliance for GPU/RAM specs
    gpu_val = specs.get("gpu") or specs.get("GPU", "")
    if gpu_val and "rtx 4090" in str(gpu_val).lower():
        items.append(AttentionItem(
            id="policy_gpu_special_justification",
            category="policy",
            severity="warning",
            message=f"GPU '{gpu_val}' requires additional Engineering Manager justification per IT Policy IT-003.",
            resolved=False
        ).model_dump())

    # Check company standard RAM compliance
    ram_val = specs.get("ram") or specs.get("RAM", "")
    if ram_val:
        try:
            resolved_policy = (
                policy_result
                if policy_result is not None
                else get_procurement_policy.invoke({
                    "item_name": draft.get("item", "General Item")
                })
            )
            max_ram = resolved_policy.get("max_specs", {}).get("ram", "")
            if max_ram and ram_val and int(''.join(filter(str.isdigit, str(ram_val)))) > int(''.join(filter(str.isdigit, str(max_ram)))):
                items.append(AttentionItem(
                    id="spec_ram",
                    category="specification",
                    severity="warning",
                    message=f"RAM '{ram_val}' exceeds company standard maximum of '{max_ram}'. Requires additional approval.",
                    resolved=False
                ).model_dump())
        except Exception as e:
            logger.warning(f"Procurement policy check failed in clarification node: {e}", exc_info=True)

    return items


# ==============================================================================
# Node Function
# ==============================================================================

async def requirement_clarification_node(state: GraphState) -> Dict[str, Any]:
    """
    LangGraph Node: Requirement Clarification Agent.

    Phase 1 additions:
    - Emits `pr` (PRArtifact) via reduce_pr_artifact (field-level merge).
    - Emits `progress` update (clarification stage).
    - Emits `agent_activity` for each tool call (append-only).
    - Emits `attention_items` for spec/policy issues (upsert by deterministic ID).

    Confirmation Rule:
    - Single Source of Truth: state['confirmation_action'] (bool).
    - Routing to Demand and `is_confirmed = True` requires confirmation_action=True AND is_complete=True.
    - If confirmation_action is True but is_complete=False, explicit feedback explains missing fields.
    """
    messages: Sequence[BaseMessage] = state.get("messages", [])
    user_context = state.get("user_context", {})
    current_draft = state.get("requirement_draft", RequirementDraftSchema().model_dump())
    last_user_message = get_last_user_message(messages)

    system_prompt = REQUIREMENT_CLARIFICATION_PROMPT.format(
        user_name=user_context.get("user_name", "User"),
        user_id=user_context.get("user_id", "usr_demo"),
        department_id=user_context.get("department_id", "DEPT-ENG"),
        cost_center=user_context.get("cost_center", "CC-ENG-001")
    )

    updated_draft = dict(current_draft)
    agent_activity: List[Dict[str, Any]] = []
    llm_response_text: str | None = None

    await emit_activity(
        "clarification.extraction",
        "requirement_extraction",
        "Understanding purchase requirement",
        "running",
    )

    # --- Pass 1: Structured extraction ---
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-3.1-flash-lite",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.1
            )
            structured_llm = llm.with_structured_output(RequirementDraftSchema)
            prompt_messages = [SystemMessage(content=system_prompt)] + list(messages)
            llm_result: RequirementDraftSchema = await structured_llm.ainvoke(prompt_messages)
            print("LLM Structured:\n", llm_result)
            extracted_dict = llm_result.model_dump()
            for k, v in extracted_dict.items():
                if v:
                    updated_draft[k] = v

            agent_activity.append(AgentAction(
                tool_name="llm_structured_extraction",
                label="Extracting requirement fields",
                status="done",
                result_summary=f"Extracted: item={updated_draft.get('item')}, qty={updated_draft.get('quantity')}"
            ).model_dump())
        except Exception as e:
            logger.warning(f"Gemini LLM extraction fallback to dynamic parser: {e}")
            updated_draft = extract_requirement_heuristics(
                last_user_message,
                current_draft,
                resolve_category=False,
            )
            agent_activity.append(AgentAction(
                tool_name="heuristic_extractor",
                label="Parsing requirement (offline mode)",
                status="done",
                result_summary=f"Heuristic: item={updated_draft.get('item')}, qty={updated_draft.get('quantity')}"
            ).model_dump())
    else:
        updated_draft = extract_requirement_heuristics(
            last_user_message,
            current_draft,
            resolve_category=False,
        )
        agent_activity.append(AgentAction(
            tool_name="heuristic_extractor",
            label="Parsing requirement (offline mode)",
            status="done",
            result_summary=f"item={updated_draft.get('item')}, qty={updated_draft.get('quantity')}"
        ).model_dump())

    await emit_activity(
        "clarification.extraction",
        "requirement_extraction",
        "Understanding purchase requirement",
        "done",
        "Requirement details extracted.",
    )

    if updated_draft.get("item") and not updated_draft.get("category"):
        category_results = await run_with_activity(
            "clarification.category",
            "get_categories",
            "Matching procurement category",
            lambda: get_categories.invoke({"query": updated_draft["item"]}),
            lambda result: (
                result[0].get("category_name", "Category matched")
                if result
                else "No matching category found"
            ),
        )
        if category_results:
            updated_draft["category"] = category_results[0]["category_name"]

    print("Updated Draft:\n", updated_draft)

    # --- Deterministic Confirmation & Routing (Single Source of Truth) ---
    is_complete = bool(updated_draft.get("is_complete"))
    is_user_confirmed = bool(state.get("confirmation_action") is True)

    if is_complete and is_user_confirmed:
        next_step = "Demand"
    else:
        next_step = "Clarification"

    # --- Phase 1: Build PRArtifact update ---
    pr_update = _build_pr_artifact_from_draft(updated_draft, user_context, is_user_confirmed)

    # --- Phase 1: Build Progress update ---
    if next_step == "Demand":
        progress_update = {"clarification": "complete", "demand_analysis": "in_progress"}
    else:
        progress_update = {"clarification": "in_progress"}

    # --- Phase 1: Build AttentionItems from spec/policy checks ---
    specs = updated_draft.get("specifications", {})
    ram_value = specs.get("ram") or specs.get("RAM", "")
    policy_result = None
    if ram_value:
        policy_result = await run_with_activity(
            "clarification.policy",
            "get_procurement_policy",
            "Checking procurement policy",
            lambda: get_procurement_policy.invoke({
                "item_name": updated_draft.get("item", "General Item")
            }),
            lambda _result: "Relevant specification policy checked.",
        )
    new_attention_items = _build_clarification_attention_items(
        updated_draft,
        user_context,
        policy_result=policy_result,
    )

    # --- Pass 2: Generate natural language response ---
    await emit_activity(
        "clarification.response",
        "response_generation",
        "Preparing assistant response",
        "running",
    )
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-3.1-flash-lite",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.7
            )
            missing_fields = []
            if not updated_draft.get("item"):
                missing_fields.append("item")
            if not updated_draft.get("quantity") or updated_draft.get("quantity", 0) <= 0:
                missing_fields.append("quantity")
            if not updated_draft.get("purpose"):
                missing_fields.append("purpose")
            if not updated_draft.get("required_date"):
                missing_fields.append("required_date")

            if is_complete and next_step == "Demand":
                response_instruction = (
                    "The user has confirmed the requirement specifications. "
                    "Acknowledge the confirmation warmly and state that you are proceeding to Demand Analysis "
                    "to check warehouse stock, organizational assets, and budget availability."
                )
            elif state.get("confirmation_action") is True and not is_complete:
                response_instruction = (
                    f"The user attempted to confirm specifications, but the requirement is incomplete. "
                    f"The following mandatory fields are still missing: {', '.join(missing_fields)}. "
                    f"Politely and explicitly inform them that the requirement cannot be confirmed yet until these fields are provided, "
                    f"and ask for the {missing_fields[0].replace('_', ' ')}."
                )
            elif is_complete:
                response_instruction = (
                    "The user's requirement details are now complete. "
                    "Write a warm, natural message confirming what you've captured (item, quantity, purpose, required date) "
                    "and ask the user to click the [Confirm Specifications] button on the summary card below "
                    "to proceed to Demand & Stock Analysis. "
                    "Do NOT say you are already proceeding yet."
                )
            else:
                response_instruction = (
                    f"The following fields are still missing or unclear: {', '.join(missing_fields)}. "
                    "Ask the user ONE focused, friendly question to gather the most important missing detail. "
                    "Do NOT list all missing fields at once. Be natural and concise."
                )

            draft_summary = str(updated_draft)
            response_prompt = [
                SystemMessage(content=(
                    f"{system_prompt}\n\n"
                    f"Current requirement draft: {draft_summary}\n\n"
                    f"Your task now: {response_instruction}"
                ))
            ] + list(messages)

            llm_response = await llm.ainvoke(response_prompt)
            llm_response_text = extract_text_from_content(llm_response.content)
        except Exception as e:
            logger.warning(f"Gemini LLM response generation failed, using fallback: {e}")
            llm_response_text = None

    # Fallback response template
    if llm_response_text:
        response_content = llm_response_text
    elif is_complete and next_step == "Demand":
        item = updated_draft.get("item", "Item")
        qty = updated_draft.get("quantity", 1)
        response_content = (
            f"Thank you for confirming! Proceeding to Demand Analysis for {qty}x {item} "
            "to check warehouse stock and organizational assets..."
        )
    elif state.get("confirmation_action") is True and not is_complete:
        missing = [f for f in ["item", "quantity", "purpose", "required_date"] if not updated_draft.get(f)]
        missing_str = ", ".join([m.replace("_", " ").title() for m in missing])
        response_content = (
            f"⚠️ **Cannot confirm specifications yet:** The following mandatory details are still missing: **{missing_str}**. "
            f"Please provide the {missing[0].replace('_', ' ')} first before confirming."
        )
    elif is_complete:
        item = updated_draft.get("item", "Item")
        qty = updated_draft.get("quantity", 1)
        purpose = updated_draft.get("purpose", "General")
        req_date = updated_draft.get("required_date", "TBD")
        specs_str = ", ".join([f"{k}: {v}" for k, v in updated_draft.get("specifications", {}).items()]) or "Standard"
        response_content = (
            f"Great! I have recorded your requirement for {qty}x {item} ({specs_str}) for {purpose}, needed by {req_date}. "
            f"Please review the summary card and click [Confirm Specifications] to proceed to Demand & Stock Analysis."
        )
    else:
        missing = [f for f in ["item", "quantity", "purpose", "required_date"] if not updated_draft.get(f)]
        response_content = f"Could you help me with {missing[0].replace('_', ' ')} for your request?" if missing else "Could you provide more details?"

    print("Final Response Content:\n", response_content)
    ai_message = AIMessage(content=response_content)

    await emit_activity(
        "clarification.response",
        "response_generation",
        "Preparing assistant response",
        "done",
        "Response is ready.",
    )

    return {
        "messages": [ai_message],
        # Phase 1 fields (via Annotated reducers)
        "pr": pr_update,
        "progress": progress_update,
        "agent_activity": agent_activity,
        "attention_items": new_attention_items,
        # Reset confirmation_action once consumed
        "confirmation_action": False,
        # DEPRECATED legacy fields — kept for backward compatibility with existing tests
        "requirement_draft": updated_draft,
        "next_agent": next_step,
    }

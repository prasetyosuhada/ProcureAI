import re
import datetime
import logging
from typing import Dict, Any, List, Sequence
from langchain_core.messages import AIMessage, SystemMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.agent.state import GraphState, RequirementDraftSchema
from app.agent.prompts import REQUIREMENT_CLARIFICATION_PROMPT
from app.tools.clarification_tools import get_categories, get_specifications, get_procurement_policy
from app.core.config import settings

logger = logging.getLogger(__name__)

CLARIFICATION_TOOLS = [get_categories, get_specifications, get_procurement_policy]

def extract_text_from_content(content: Any) -> str:
    """Safely extracts clean plain text from LangChain message content (handles str, list of dicts, or nested blocks)."""
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

def extract_requirement_heuristics(user_text: str, current_draft: Dict[str, Any]) -> Dict[str, Any]:
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

    # 1. Dynamic Item & Category Extraction (Works for ANY item)
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
            # Match 'need/want/buy/order [quantity] <ITEM> for/before/with...'
            item_match = re.search(
                r'\b(?:need|want|buy|request|order|purchasing|for)\s+(?:to\s+buy\s+)?(?:a|an|\$[\d,]+|\d+)?\s*(?:a|an|\$[\d,]+|\d+)?\s*([a-zA-Z0-9\s\-/]{2,35}?)(?=\s+(?:for|before|by|with|to|in|\.)\b|[.,;]|$)',
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

    # Default category resolution using get_categories tool
    if draft.get("item") and not draft.get("category"):
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

    # 3. Extract Purpose / Workload
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

    # 4. Extract Specifications (RAM, Storage, general specs)
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


async def requirement_clarification_node(state: GraphState) -> Dict[str, Any]:
    """
    LangGraph Node function for the Requirement Clarification Agent.
    Uses REQUIREMENT_CLARIFICATION_PROMPT with Gemini LLM and bound tools, with dynamic fallback.
    """
    messages: Sequence[BaseMessage] = state.get("messages", [])
    user_context = state.get("user_context", {})
    current_draft = state.get("requirement_draft", RequirementDraftSchema().model_dump())
    last_user_message = get_last_user_message(messages)

    # Format the REQUIREMENT_CLARIFICATION_PROMPT with user context
    system_prompt = REQUIREMENT_CLARIFICATION_PROMPT.format(
        user_name=user_context.get("user_name", "User"),
        user_id=user_context.get("user_id", "usr_demo"),
        department_id=user_context.get("department_id", "DEPT-ENG"),
        cost_center=user_context.get("cost_center", "CC-ENG-001")
    )

    updated_draft = dict(current_draft)

    llm_response_text: str | None = None

    # Invoke Gemini LLM if API Key is configured
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-3.1-flash-lite",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.1
            )
            # --- Pass 1: Structured extraction ---
            structured_llm = llm.with_structured_output(RequirementDraftSchema)
            prompt_messages = [SystemMessage(content=system_prompt)] + list(messages)
            llm_result: RequirementDraftSchema = await structured_llm.ainvoke(prompt_messages)
            print("LLM Structured:\n", llm_result)

            extracted_dict = llm_result.model_dump()
            for k, v in extracted_dict.items():
                if v:
                    updated_draft[k] = v
        except Exception as e:
            logger.warning(f"Gemini LLM extraction fallback to dynamic parser: {e}")
            updated_draft = extract_requirement_heuristics(last_user_message, current_draft)
    else:
        updated_draft = extract_requirement_heuristics(last_user_message, current_draft)
    print("Updated Draft:\n", updated_draft)

    # Determine next routing step based on completeness
    next_step = "Demand" if updated_draft.get("is_complete") else "Clarification"

    # --- Pass 2: Generate natural language response via LLM ---
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

            if next_step == "Demand":
                response_instruction = (
                    "The user's requirement is now complete. "
                    "Write a warm, natural confirmation message summarizing what you've captured — "
                    "item, category, quantity, purpose, specifications, and required date — "
                    "and mention that you are proceeding to Demand Analysis to check warehouse stock and organizational assets. "
                    "Write it conversationally and naturally."
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

    # Fallback to simple template if LLM response generation failed
    if llm_response_text:
        response_content = llm_response_text
    elif next_step == "Demand":
        item = updated_draft.get("item", "Item")
        qty = updated_draft.get("quantity", 1)
        purpose = updated_draft.get("purpose", "General")
        req_date = updated_draft.get("required_date", "TBD")
        specs_str = ", ".join([f"{k}: {v}" for k, v in updated_draft.get("specifications", {}).items()]) or "Standard"
        response_content = (
            f"Thank you! I have recorded your finalized requirement:\n\n"
            f"• **Item:** {item}\n"
            f"• **Category:** {updated_draft.get('category', 'General')}\n"
            f"• **Quantity:** {qty}\n"
            f"• **Purpose:** {purpose}\n"
            f"• **Specifications:** {specs_str}\n"
            f"• **Required Date:** {req_date}\n\n"
            f"Proceeding to Demand Analysis to check warehouse stock and organizational assets..."
        )
    else:
        missing = [f for f in ["item", "quantity", "purpose", "required_date"] if not updated_draft.get(f)]
        response_content = f"Could you help me with {missing[0].replace('_', ' ')} for your request?" if missing else "Could you provide more details?"

    ai_message = AIMessage(content=response_content)
    print("AI Message:\n", ai_message)

    return {
        "messages": [ai_message],
        "requirement_draft": updated_draft,
        "next_agent": next_step
    }

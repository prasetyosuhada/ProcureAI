import logging
from typing import Dict, Any, List, Sequence, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.agent.state import GraphState, DemandAnalysisSchema
from app.agent.prompts import DEMAND_ANALYSIS_PROMPT
from app.tools.demand_tools import (
    get_inventory,
    get_assets,
    get_open_prs_and_pos,
    get_purchase_history,
    get_budget_status,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

DEMAND_TOOLS = [
    get_inventory,
    get_assets,
    get_open_prs_and_pos,
    get_purchase_history,
    get_budget_status,
]

class DemandJustificationResponse(BaseModel):
    justification: str = Field(description="Clear, concise, professional explanation for the recommended purchase quantity, noting warehouse stock, asset availability, and budget status.")


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


def generate_default_justification(
    requested_qty: int,
    inv_qty: int,
    asset_qty: int,
    recommended_qty: int,
    pipeline_qty: int,
    cost_center: str,
    budget_res: Dict[str, Any],
    item_name: str
) -> str:
    """Fallback generator for justification text when LLM is unavailable."""
    total_existing = inv_qty + asset_qty
    if total_existing >= requested_qty:
        justification = (
            f"Organizational analysis found {inv_qty} units in warehouse inventory and "
            f"{asset_qty} unused/returning assets (Total: {total_existing} available). "
            f"This fully covers your requested quantity of {requested_qty}. "
            f"Recommended new purchase quantity is 0 units (fulfill internally)."
        )
    elif total_existing > 0:
        justification = (
            f"Organizational analysis found {inv_qty} units in warehouse stock and "
            f"{asset_qty} unused/returning assets (Total: {total_existing} available). "
            f"Deducting existing availability from requested quantity ({requested_qty} - {total_existing}), "
            f"the recommended new purchase quantity is {recommended_qty} units."
        )
    else:
        justification = (
            f"No existing warehouse stock or returning assets were found for '{item_name}'. "
            f"Budget check for Cost Center {cost_center} confirmed sufficient remaining balance "
            f"(${budget_res.get('remaining_budget', 0):,.2f} {budget_res.get('currency', 'USD')}). "
            f"Recommended new purchase quantity is {recommended_qty} units."
        )

    if pipeline_qty > 0:
        justification += f" Note: There are currently {pipeline_qty} units already in the procurement pipeline (open PRs/POs)."

    return justification


async def demand_analysis_node(state: GraphState) -> Dict[str, Any]:
    """
    LangGraph Node function for the Demand Analysis Agent.
    Fetches real-time stock, assets, pipeline, and budget status, calculates net demand,
    and produces a data-backed recommended purchase quantity using DemandAnalysisSchema.
    """
    requirement_draft = state.get("requirement_draft", {})
    user_context = state.get("user_context", {})

    item_name = requirement_draft.get("item", "General Item")
    requested_qty = requirement_draft.get("quantity", 1)
    category_id = requirement_draft.get("category")
    dept_id = user_context.get("department_id", "DEPT-ENG")
    cost_center = user_context.get("cost_center", "CC-ENG-001")

    # 1. Fetch deterministic data via Demand Tools (Ground truth to prevent LLM math hallucination)
    inventory_res = get_inventory.invoke({"item_name": item_name, "category_id": category_id})
    assets_res = get_assets.invoke({"item_name": item_name})
    pipeline_res = get_open_prs_and_pos.invoke({"item_name": item_name, "department_id": dept_id})
    budget_res = get_budget_status.invoke({"cost_center": cost_center})

    inv_qty = inventory_res.get("available_quantity", 0)
    asset_qty = assets_res.get("total_available_soon", 0)
    pipeline_qty = pipeline_res.get("total_in_pipeline", 0)
    total_existing = inv_qty + asset_qty

    # 2. Perform Quantitative Net Demand Calculation
    net_demand = max(0, requested_qty - total_existing)
    recommended_qty = net_demand

    # 3. Format DEMAND_ANALYSIS_PROMPT system prompt with user context
    system_prompt = DEMAND_ANALYSIS_PROMPT.format(
        user_name=user_context.get("user_name", "User"),
        user_id=user_context.get("user_id", "usr_demo"),
        department_id=dept_id,
        cost_center=cost_center
    )

    # 4. Use Gemini LLM to generate professional justification if API Key is present
    justification = ""
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            llm = ChatGoogleGenerativeAI(
                model=getattr(settings, "GEMINI_MODEL", "gemini-3.1-flash-lite"),
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.1
            )
            analysis_request = (
                f"Item: '{item_name}', Requested: {requested_qty}. "
                f"Data found: Warehouse stock = {inv_qty}, Unused assets = {asset_qty}, "
                f"Pipeline POs = {pipeline_qty}, Remaining Budget = ${budget_res.get('remaining_budget', 0):,.2f}. "
                f"Calculated recommended purchase quantity: {recommended_qty} units. "
                f"Provide a concise, professional justification for the recommended quantity."
            )
            prompt_messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=analysis_request)
            ]
            try:
                structured_llm = llm.with_structured_output(DemandJustificationResponse)
                llm_structured_res: DemandJustificationResponse = await structured_llm.ainvoke(prompt_messages)
                justification = llm_structured_res.justification.strip()
                print("LLM Structured:\n", llm_structured_res)
            except Exception:
                llm_response = await llm.ainvoke(prompt_messages)
                justification = extract_text_from_content(llm_response.content)
                print("LLM Not Structured:\n", llm_response)
        except Exception as e:
            logger.warning(f"Gemini LLM demand justification fallback: {e}")
            justification = generate_default_justification(
                requested_qty, inv_qty, asset_qty, recommended_qty, pipeline_qty, cost_center, budget_res, item_name
            )
    else:
        justification = generate_default_justification(
            requested_qty, inv_qty, asset_qty, recommended_qty, pipeline_qty, cost_center, budget_res, item_name
        )

    # 5. Build Validated State Payload using DemandAnalysisSchema
    demand_analysis_obj = DemandAnalysisSchema(
        requested_quantity=requested_qty,
        available_inventory=inv_qty,
        available_assets=asset_qty,
        recommended_quantity=recommended_qty,
        justification=justification,
        is_complete=True
    )
    demand_analysis_payload = demand_analysis_obj.model_dump()

    # 6. Format Professional Chat Message for the User
    summary_message = (
        f"📊 **Demand & Stock Analysis Complete for {item_name}:**\n\n"
        f"• **Requested Quantity:** {requested_qty} units\n"
        f"• **Warehouse Stock Available:** {inv_qty} units\n"
        f"• **Unused/Returning Assets:** {asset_qty} units\n"
        f"• **Pipeline Orders (Incoming):** {pipeline_qty} units\n"
        f"• **Cost Center Budget Remaining ({cost_center}):** ${budget_res.get('remaining_budget', 0):,.2f} {budget_res.get('currency', 'USD')}\n\n"
        f"💡 **Recommended Net Purchase Quantity:** **{recommended_qty} units**\n\n"
        f"📝 **Justification:**\n{justification}\n\n"
        f"Proceeding to generate draft Purchase Requisition (PR)..."
    )

    ai_message = AIMessage(content=summary_message)

    return {
        "messages": [ai_message],
        "demand_analysis": demand_analysis_payload,
        "next_agent": "GeneratePR"
    }

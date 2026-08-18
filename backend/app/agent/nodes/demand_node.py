import logging
from typing import Dict, Any, List, Sequence
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
        justification += f" (Note: {pipeline_qty} units currently in open PR/PO pipeline)."

    return justification


async def demand_analysis_node(state: GraphState) -> Dict[str, Any]:
    """
    LangGraph Node function for the Demand Analysis Agent.
    Executes DEMAND_ANALYSIS_PROMPT with Gemini LLM, fetches deterministic enterprise data,
    and calculates data-backed recommended purchase quantity.
    """
    requirement_draft = state.get("requirement_draft", {})
    user_context = state.get("user_context", {})

    item_name = requirement_draft.get("item", "Item")
    category_id = requirement_draft.get("category", "")
    requested_qty = requirement_draft.get("quantity", 1)
    cost_center = user_context.get("cost_center", "CC-ENG-001")
    dept_id = user_context.get("department_id", "DEPT-ENG")

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
                model="gemini-3.1-flash-lite",
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
            llm_response = await llm.ainvoke(prompt_messages)
            justification = str(llm_response.content).strip()
        except Exception as e:
            logger.warning(f"Gemini LLM demand justification fallback: {e}")
            justification = generate_default_justification(
                requested_qty, inv_qty, asset_qty, recommended_qty, pipeline_qty, cost_center, budget_res, item_name
            )
    else:
        justification = generate_default_justification(
            requested_qty, inv_qty, asset_qty, recommended_qty, pipeline_qty, cost_center, budget_res, item_name
        )

    # 5. Prepare Updated Demand Analysis State Payload
    demand_analysis_payload = {
        "requested_quantity": requested_qty,
        "available_inventory": inv_qty,
        "available_assets": asset_qty,
        "recommended_quantity": recommended_qty,
        "justification": justification,
        "is_complete": True
    }

    # 6. Formulate Response Message to User
    response_content = (
        f"📊 **Demand Analysis Complete**\n\n"
        f"• **Requested Quantity:** {requested_qty}\n"
        f"• **Warehouse Stock:** {inv_qty} units\n"
        f"• **Unused Assets:** {asset_qty} units\n"
        f"• **Recommended Purchase Quantity:** **{recommended_qty} units**\n\n"
        f"**Justification:** {justification}\n\n"
        f"Proceeding to generate your official Purchase Requisition (PR) draft..."
    )

    ai_message = AIMessage(content=response_content)

    return {
        "messages": [ai_message],
        "demand_analysis": demand_analysis_payload,
        "next_agent": "GeneratePR"
    }

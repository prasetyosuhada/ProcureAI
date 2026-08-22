import logging
from typing import Dict, Any, List, Sequence, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.agent.state import (
    GraphState,
    DemandAnalysisSchema,
    DemandBreakdown,
    AgentAction,
    AttentionItem,
)
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
    justification: str = Field(
        description="Clear, concise, professional explanation for the recommended purchase quantity, "
                    "noting warehouse stock, asset availability, and budget status."
    )


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
        justification += (
            f" Note: There are currently {pipeline_qty} units already in the procurement pipeline (open PRs/POs)."
        )

    return justification


def _build_demand_attention_items(
    recommended_qty: int,
    budget_res: Dict[str, Any],
    cost_center: str,
    purchase_history: Dict[str, Any],
    item_name: str,
) -> List[Dict[str, Any]]:
    """
    Generates budget & policy AttentionItems from demand analysis data.
    IDs are deterministic: budget_{cost_center}, policy_{rule_key}.
    """
    items: List[Dict[str, Any]] = []
    remaining = budget_res.get("remaining_budget", 0)
    avg_cost = purchase_history.get("average_unit_cost", 0)
    estimated_total = avg_cost * recommended_qty if avg_cost and recommended_qty else 0

    # Budget check: estimated cost vs remaining budget
    if estimated_total > 0 and remaining > 0 and estimated_total > remaining:
        deficit = estimated_total - remaining
        items.append(AttentionItem(
            id=f"budget_{cost_center.lower()}",
            category="budget",
            severity="blocking",
            message=(
                f"Estimated cost for {recommended_qty}x {item_name} "
                f"(~${estimated_total:,.0f}) exceeds remaining Q-budget for {cost_center} "
                f"by ${deficit:,.0f}. Additional budget approval required before submission."
            ),
            resolved=False
        ).model_dump())
    elif estimated_total > 0 and remaining > 0 and estimated_total > (remaining * 0.8):
        items.append(AttentionItem(
            id=f"budget_{cost_center.lower()}",
            category="budget",
            severity="warning",
            message=(
                f"This purchase (~${estimated_total:,.0f}) will consume more than 80% of remaining "
                f"budget for {cost_center}. Proceed with awareness."
            ),
            resolved=False
        ).model_dump())

    # Policy check: approval threshold
    approval_threshold = budget_res.get("approval_threshold", 0)
    if approval_threshold and estimated_total > approval_threshold:
        items.append(AttentionItem(
            id="policy_vp_approval_threshold",
            category="policy",
            severity="warning",
            message=(
                f"Total estimated cost ${estimated_total:,.0f} exceeds approval threshold "
                f"${approval_threshold:,.0f}. VP-level sign-off required per Procurement Policy."
            ),
            resolved=False
        ).model_dump())

    return items


# ==============================================================================
# Node Function
# ==============================================================================

async def demand_analysis_node(state: GraphState) -> Dict[str, Any]:
    """
    LangGraph Node: Demand Analysis Agent.

    Phase 1 additions:
    - Emits `demand` (DemandBreakdown) via reduce_demand (shallow merge).
    - Emits `progress` update (demand_analysis + validation stages).
    - Emits `agent_activity` for each tool call (append-only).
    - Emits `attention_items` for budget/policy issues (upsert by deterministic ID).

    Manual Override & Stale Detection:
    - If state['demand']['is_manually_overridden'] is True, this node preserves the user's
      manual net_new_purchase quantity instead of overwriting it with recalculated numbers.
    - If underlying inventory, assets, or pipeline numbers have changed since the override,
      it emits an AttentionItem (id=override_stale_{cost_center}) to warn the user.

    Legacy backward compatibility:
    - Still writes to `demand_analysis` (DEPRECATED: do not rely in new code).
    """
    requirement_draft = state.get("requirement_draft", {})
    user_context = state.get("user_context", {})
    existing_demand = state.get("demand") or {}

    item_name = requirement_draft.get("item", "General Item")
    requested_qty = requirement_draft.get("quantity", 1)
    category_id = requirement_draft.get("category")
    dept_id = user_context.get("department_id", "DEPT-ENG")
    cost_center = user_context.get("cost_center", "CC-ENG-001")

    agent_activity: List[Dict[str, Any]] = []

    # 1. Fetch deterministic data via Demand Tools (ground truth; prevents LLM math hallucination)
    inventory_res = get_inventory.invoke({"item_name": item_name, "category_id": category_id})
    agent_activity.append(AgentAction(
        tool_name="get_inventory",
        label="Checking warehouse inventory",
        status="done",
        result_summary=f"{inventory_res.get('available_quantity', 0)} units in stock"
    ).model_dump())

    assets_res = get_assets.invoke({"item_name": item_name})
    agent_activity.append(AgentAction(
        tool_name="get_assets",
        label="Scanning idle & returning assets",
        status="done",
        result_summary=f"{assets_res.get('total_available_soon', 0)} assignable assets found"
    ).model_dump())

    pipeline_res = get_open_prs_and_pos.invoke({"item_name": item_name, "department_id": dept_id})
    agent_activity.append(AgentAction(
        tool_name="get_open_prs_and_pos",
        label="Checking open PRs & POs in pipeline",
        status="done",
        result_summary=f"{pipeline_res.get('total_in_pipeline', 0)} units already in pipeline"
    ).model_dump())

    budget_res = get_budget_status.invoke({"cost_center": cost_center})
    agent_activity.append(AgentAction(
        tool_name="get_budget_status",
        label="Verifying department budget",
        status="done",
        result_summary=f"${budget_res.get('remaining_budget', 0):,.0f} remaining in {cost_center}"
    ).model_dump())

    purchase_history = get_purchase_history.invoke({"item_name": item_name, "department_id": dept_id})
    agent_activity.append(AgentAction(
        tool_name="get_purchase_history",
        label="Reviewing 12-month purchase history",
        status="done",
        result_summary=f"Avg unit cost: ${purchase_history.get('average_unit_cost', 0):,.0f}"
    ).model_dump())

    inv_qty = inventory_res.get("available_quantity", 0)
    asset_qty = assets_res.get("total_available_soon", 0)
    pipeline_qty = pipeline_res.get("total_in_pipeline", 0)
    total_existing = inv_qty + asset_qty

    # 2. Quantitative Net Demand Calculation
    net_demand = max(0, requested_qty - total_existing)
    recommended_qty = net_demand

    # 3. Manual Override Protection (resolved at node level)
    is_manually_overridden = existing_demand.get("is_manually_overridden", False)
    override_reason = existing_demand.get("override_reason")
    if is_manually_overridden:
        # Use the user's manually set quantity instead of recalculated recommendation
        recommended_qty = existing_demand.get("net_new_purchase", recommended_qty)
        logger.info(
            f"[demand_analysis_node] Manual override active: using net_new_purchase={recommended_qty} "
            f"(reason: {override_reason}). Calculated value {net_demand} was NOT applied."
        )

    # 4. System prompt format
    system_prompt = DEMAND_ANALYSIS_PROMPT.format(
        user_name=user_context.get("user_name", "User"),
        user_id=user_context.get("user_id", "usr_demo"),
        department_id=dept_id,
        cost_center=cost_center
    )

    # 5. Gemini LLM: Generate professional justification
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
                f"Calculated recommended purchase quantity: {recommended_qty} units."
                + (f" NOTE: User has manually overridden this quantity (override reason: {override_reason})." if is_manually_overridden else "")
                + " Provide a concise, professional justification."
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

    # 6. Build Phase 1 DemandBreakdown payload
    estimated_saving = float(purchase_history.get("average_unit_cost", 0) * total_existing) if total_existing > 0 else None
    demand_breakdown = DemandBreakdown(
        requested_qty=requested_qty,
        existing_inventory=inv_qty,
        assignable_assets=asset_qty,
        reserved_qty=pipeline_qty,
        net_new_purchase=recommended_qty,
        estimated_saving=estimated_saving,
        is_manually_overridden=is_manually_overridden,
        override_reason=override_reason,
    )
    demand_payload = demand_breakdown.model_dump()

    # 7. Build Progress update
    progress_update = {
        "demand_analysis": "complete",
        "validation": "in_progress",  # waiting for user Accept/Modify/Reject on recommendation
    }

    # 8. Build AttentionItems from budget/policy checks and stale override detection
    new_attention_items = _build_demand_attention_items(
        recommended_qty=recommended_qty,
        budget_res=budget_res,
        cost_center=cost_center,
        purchase_history=purchase_history,
        item_name=item_name,
    )

    # Check for stale manual override:
    # If is_manually_overridden is True, compare freshly fetched inventory/asset/pipeline data with the previous state in existing_demand
    if is_manually_overridden and existing_demand:
        old_inv = existing_demand.get("existing_inventory")
        old_assets = existing_demand.get("assignable_assets")
        old_reserved = existing_demand.get("reserved_qty")
        
        if (
            (old_inv is not None and old_inv != inv_qty)
            or (old_assets is not None and old_assets != asset_qty)
            or (old_reserved is not None and old_reserved != pipeline_qty)
        ):
            stale_item = AttentionItem(
                id=f"override_stale_{cost_center.lower()}",
                category="specification",
                severity="warning",
                message=(
                    f"Underlying inventory/asset data has changed since your manual override "
                    f"of net_new_purchase to {existing_demand.get('net_new_purchase')}. "
                    f"Please review whether this quantity is still accurate."
                ),
                resolved=False
            ).model_dump()
            new_attention_items.append(stale_item)

    # 9. Build legacy DemandAnalysisSchema (for backward compat with tests)
    demand_analysis_obj = DemandAnalysisSchema(
        requested_quantity=requested_qty,
        available_inventory=inv_qty,
        available_assets=asset_qty,
        recommended_quantity=recommended_qty,
        justification=justification,
        is_complete=True
    )
    demand_analysis_payload = demand_analysis_obj.model_dump()

    # 10. Format chat message for user
    manually_overridden_note = (
        f"\n> ⚠️ **Note:** Net purchase quantity was manually adjusted by you to **{recommended_qty} units** "
        f"(reason: _{override_reason}_)."
        if is_manually_overridden else ""
    )
    summary_message = (
        f"📊 **Demand & Stock Analysis Complete for {item_name}:**\n\n"
        f"• **Requested Quantity:** {requested_qty} units\n"
        f"• **Warehouse Stock Available:** {inv_qty} units\n"
        f"• **Unused/Returning Assets:** {asset_qty} units\n"
        f"• **Pipeline Orders (Incoming):** {pipeline_qty} units\n"
        f"• **Cost Center Budget Remaining ({cost_center}):** ${budget_res.get('remaining_budget', 0):,.2f} {budget_res.get('currency', 'USD')}\n\n"
        f"💡 **Recommended Net Purchase Quantity:** **{recommended_qty} units**\n"
        f"{manually_overridden_note}\n"
        f"📝 **Justification:**\n{justification}\n\n"
        f"Please review the Demand Analysis panel and choose to **Accept**, **Modify**, or **Reject** the recommendation."
    )

    ai_message = AIMessage(content=summary_message)

    return {
        "messages": [ai_message],
        # Phase 1 fields (via Annotated reducers)
        "demand": demand_payload,
        "progress": progress_update,
        "agent_activity": agent_activity,
        "attention_items": new_attention_items,
        # Also update PR quantity with recommended_qty
        "pr": {"quantity": recommended_qty},
        # DEPRECATED legacy fields — kept for backward compatibility with existing tests
        "demand_analysis": demand_analysis_payload,
        "next_agent": "GeneratePR",
    }

import datetime
import uuid
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.messages import AIMessage, HumanMessage
from app.schemas.user_context import UserContext
from app.api.deps import get_current_user_context
from app.agent.graph import get_compiled_procure_graph
from app.agent.state import create_initial_graph_state
from app.schemas.requests import (
    RecommendationActionRequest,
    ConfirmSpecificationsResponse,
    ResolveAttentionResponse,
    SubmitPRRequest,
    SubmitPRResponse,
    RequestStateResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/requests", tags=["Procurement Requests"])


# ==============================================================================
# 1. GET /api/v1/requests/{id}/state
# ==============================================================================
@router.get("/{id}/state", response_model=RequestStateResponse)
async def get_request_state(
    id: str,
    user_context: UserContext = Depends(get_current_user_context),
) -> RequestStateResponse:
    """
    Retrieves full state snapshot for hydrating the UI upon page reload or session resumption.
    Reads directly from LangGraph checkpoint state based on thread_id.
    """
    try:
        graph = await get_compiled_procure_graph()
        config = {"configurable": {"thread_id": id}}
        snapshot = await graph.aget_state(config)

        if not snapshot or not snapshot.values:
            initial = create_initial_graph_state(user_context.model_dump())
            return RequestStateResponse(
                thread_id=id,
                pr=initial["pr"],
                progress=initial["progress"],
                demand=initial["demand"],
                agent_activity=initial["agent_activity"],
                attention_items=initial["attention_items"],
                recommendation_status=initial["recommendation_status"],
                messages=[],
                last_message=None,
                next_agent=initial["next_agent"]
            )

        vals = snapshot.values
        raw_messages = vals.get("messages", [])
        serialized_messages = []
        last_msg = None

        for m in raw_messages:
            role = "assistant" if getattr(m, "type", None) == "ai" or getattr(m, "role", None) == "assistant" else "user"
            content = str(getattr(m, "content", ""))
            serialized_messages.append({"role": role, "content": content})
            if role == "assistant":
                last_msg = content

        return RequestStateResponse(
            thread_id=id,
            pr=vals.get("pr", {}),
            progress=vals.get("progress", {}),
            demand=vals.get("demand"),
            agent_activity=vals.get("agent_activity", []),
            attention_items=vals.get("attention_items", []),
            recommendation_status=vals.get("recommendation_status", "none"),
            messages=serialized_messages,
            last_message=last_msg,
            next_agent=vals.get("next_agent", "Clarification")
        )
    except Exception as e:
        logger.error(f"Error fetching state for thread {id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch request state for thread {id}"
        )


# ==============================================================================
# 2. POST /api/v1/requests/{id}/confirm-specifications
# ==============================================================================
@router.post("/{id}/confirm-specifications", response_model=ConfirmSpecificationsResponse)
async def confirm_specifications(
    id: str,
    user_context: UserContext = Depends(get_current_user_context),
) -> ConfirmSpecificationsResponse:
    """
    Explicit action endpoint to confirm extracted specifications (triggered by UI [Confirm Specifications] button).
    Invokes the graph with confirmation_action=True.
    """
    try:
        graph = await get_compiled_procure_graph()
        config = {"configurable": {"thread_id": id}}

        input_payload = {
            "messages": [HumanMessage(content="Specifications confirmed.")],
            "confirmation_action": True,
            "user_context": user_context.model_dump()
        }

        result = await graph.ainvoke(input_payload, config=config)

        # Extract last AI message content
        ai_msg = "Specifications confirmed. Proceeding to Demand Analysis."
        for m in reversed(result.get("messages", [])):
            if getattr(m, "type", None) == "ai" or getattr(m, "role", None) == "assistant":
                ai_msg = str(m.content)
                break

        is_confirmed = (
            result.get("next_agent") == "Demand" 
            or result.get("progress", {}).get("clarification") == "complete"
        )

        return ConfirmSpecificationsResponse(
            thread_id=id,
            is_confirmed=is_confirmed,
            message=ai_msg,
            next_agent=result.get("next_agent", "Clarification"),
            pr=result.get("pr", {}),
            progress=result.get("progress", {}),
            attention_items=result.get("attention_items", [])
        )
    except Exception as e:
        logger.error(f"Error confirming specifications for thread {id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm specifications for thread {id}"
        )


# ==============================================================================
# 3. POST /api/v1/requests/{id}/recommendation
# ==============================================================================
@router.post("/{id}/recommendation", response_model=RequestStateResponse)
async def handle_recommendation_action(
    id: str,
    payload: RecommendationActionRequest,
    user_context: UserContext = Depends(get_current_user_context),
) -> RequestStateResponse:
    """
    Decision endpoint for AI Demand Recommendation (Option A - Pure State Mutation).
    Handles:
    - 'accept': Promotes the recommended net-new quantity to the final PR quantity and marks validation complete.
    - 'keep_original': Explicitly retains the requested quantity as the final PR quantity.
    - 'modify': Directly patches net_new_purchase quantity with is_manually_overridden=True and notes.
    - 'reject': Marks recommendation rejected and pauses/cancels requisition.

    Guards:
    - Rejects if Demand Analysis has not been executed yet (state['demand'] is None).
    - Rejects if PR is already submitted.
    - Validates non-negative quantity for 'modify'.
    """
    try:
        graph = await get_compiled_procure_graph()
        config = {"configurable": {"thread_id": id}}
        snapshot = await graph.aget_state(config)

        if not snapshot or not snapshot.values:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Procurement request thread '{id}' not found."
            )

        current_vals = dict(snapshot.values)
        current_demand = current_vals.get("demand")
        current_pr = dict(current_vals.get("pr") or {})

        # Guard 1: Demand Analysis must have been performed before acting on recommendation
        if current_demand is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No demand analysis available yet. Cannot act on recommendation before Demand Analysis is performed."
            )

        # Guard 2: Requisition already submitted cannot be modified
        if current_pr.get("status") == "submitted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify recommendation: Purchase Requisition has already been submitted."
            )

        updated_demand = dict(current_demand)

        if payload.action == "modify":
            if not payload.modification or payload.modification.net_new_purchase is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Modification details ('net_new_purchase') are required for action 'modify'."
                )

            new_qty = payload.modification.net_new_purchase
            if new_qty < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Purchase quantity ('net_new_purchase') cannot be negative."
                )

            notes = payload.modification.user_notes or "Manually adjusted by user"

            updated_demand["net_new_purchase"] = new_qty
            updated_demand["is_manually_overridden"] = True
            updated_demand["override_reason"] = notes
            current_pr["quantity"] = new_qty

            patch = {
                "demand": updated_demand,
                "pr": current_pr,
                "recommendation_status": "modified",
                "progress": {
                    "validation": "complete",
                    "ready_for_submission": "in_progress"
                },
                "messages": [
                    AIMessage(
                        content=f"✅ Quantity recommendation manually updated to **{new_qty} units** "
                                f"(Reason: _{notes}_). Ready for final review."
                    )
                ]
            }
            await graph.aupdate_state(config, patch)

        elif payload.action == "keep_original":
            original_qty = current_demand["requested_qty"]
            override_reason = "User chose to keep original requested quantity"
            updated_demand["net_new_purchase"] = original_qty
            updated_demand["is_manually_overridden"] = True
            updated_demand["override_reason"] = override_reason
            current_pr["quantity"] = original_qty

            patch = {
                "demand": updated_demand,
                "pr": current_pr,
                "recommendation_status": "kept_original",
                "progress": {
                    "validation": "complete",
                    "ready_for_submission": "in_progress"
                },
                "messages": [
                    AIMessage(
                        content=f"✅ Original requested quantity retained at **{original_qty} units**. "
                                "Ready for final review."
                    )
                ]
            }
            await graph.aupdate_state(config, patch)

        elif payload.action == "accept":
            # Accepting the recommendation is the explicit user decision that
            # turns the net-new purchase quantity into the final PR quantity.
            current_pr["quantity"] = current_demand["net_new_purchase"]
            patch = {
                "recommendation_status": "accepted",
                "pr": current_pr,
                "progress": {
                    "validation": "complete",
                    "ready_for_submission": "in_progress"
                },
                "messages": [
                    AIMessage(content="✅ Demand recommendation accepted. Ready for final review and submission.")
                ]
            }
            await graph.aupdate_state(config, patch)

        elif payload.action == "reject":
            # Rejection cancels the recommendation and restores the original
            # requested quantity; the rejected status prevents submission.
            current_pr["quantity"] = current_demand["requested_qty"]
            current_pr["status"] = "rejected"
            patch = {
                "recommendation_status": "rejected",
                "progress": {
                    "validation": "blocked",
                    "ready_for_submission": "blocked"
                },
                "pr": current_pr,
                "messages": [
                    AIMessage(content="🛑 Demand recommendation was rejected by user. The procurement request has been paused.")
                ]
            }
            await graph.aupdate_state(config, patch)

        # Retrieve fresh updated state snapshot
        updated_snapshot = await graph.aget_state(config)
        updated_vals = updated_snapshot.values
        raw_messages = updated_vals.get("messages", [])
        serialized_messages = []
        last_msg = None

        for m in raw_messages:
            role = "assistant" if getattr(m, "type", None) == "ai" or getattr(m, "role", None) == "assistant" else "user"
            content = str(getattr(m, "content", ""))
            serialized_messages.append({"role": role, "content": content})
            if role == "assistant":
                last_msg = content

        return RequestStateResponse(
            thread_id=id,
            pr=updated_vals.get("pr", {}),
            progress=updated_vals.get("progress", {}),
            demand=updated_vals.get("demand"),
            agent_activity=updated_vals.get("agent_activity", []),
            attention_items=updated_vals.get("attention_items", []),
            recommendation_status=updated_vals.get("recommendation_status", "none"),
            messages=serialized_messages,
            last_message=last_msg,
            next_agent=updated_vals.get("next_agent", "Clarification")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling recommendation for thread {id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process recommendation action for thread {id}"
        )


# ==============================================================================
# 4. POST /api/v1/requests/{id}/attention/{item_id}/resolve
# ==============================================================================
@router.post("/{id}/attention/{item_id}/resolve", response_model=ResolveAttentionResponse)
async def resolve_attention_item(
    id: str,
    item_id: str,
    user_context: UserContext = Depends(get_current_user_context),
) -> ResolveAttentionResponse:
    """
    Marks an attention item as resolved: True.
    Protected from overwrite on subsequent node re-runs via reduce_attention_items.
    """
    try:
        graph = await get_compiled_procure_graph()
        config = {"configurable": {"thread_id": id}}
        snapshot = await graph.aget_state(config)

        if not snapshot or not snapshot.values:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Procurement request thread '{id}' not found."
            )

        current_vals = snapshot.values
        attention_items = [dict(item) for item in current_vals.get("attention_items", [])]
        found = False

        for item in attention_items:
            if item.get("id") == item_id:
                item["resolved"] = True
                found = True
                break

        if not found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attention item '{item_id}' not found in request state."
            )

        await graph.aupdate_state(config, {"attention_items": attention_items})

        unresolved_blocking = sum(
            1 for item in attention_items 
            if item.get("severity") == "blocking" and not item.get("resolved")
        )

        return ResolveAttentionResponse(
            thread_id=id,
            resolved_item_id=item_id,
            message=f"Attention item '{item_id}' marked as resolved.",
            attention_items=attention_items,
            blocking_count=unresolved_blocking
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving attention item {item_id} for thread {id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve attention item {item_id}"
        )


# ==============================================================================
# 5. POST /api/v1/requests/{id}/submit
# ==============================================================================
@router.post("/{id}/submit", response_model=SubmitPRResponse)
async def submit_purchase_requisition(
    id: str,
    payload: Optional[SubmitPRRequest] = None,
    user_context: UserContext = Depends(get_current_user_context),
) -> SubmitPRResponse:
    """
    Final PR Submission endpoint with backend guards:
    - Guard 1: Rejects submission if there are unresolved blocking attention items.
    - Guard 2: Validates presence of item name and positive quantity.
    - Guard 3: Validates recommendation_status is 'accepted', 'kept_original', or 'modified' (rejects 'none', 'pending_review', 'rejected').
    - Guard 4: Rejects submission if PR is already submitted.
    """
    try:
        graph = await get_compiled_procure_graph()
        config = {"configurable": {"thread_id": id}}
        snapshot = await graph.aget_state(config)

        if not snapshot or not snapshot.values:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Procurement request thread '{id}' not found."
            )

        vals = snapshot.values
        pr_data = dict(vals.get("pr") or {})
        progress_data = dict(vals.get("progress") or {})
        attention_items = vals.get("attention_items", [])
        rec_status = vals.get("recommendation_status", "none")

        # Guard 1: Check for unresolved blocking attention items
        unresolved_blocking = [
            item for item in attention_items 
            if item.get("severity") == "blocking" and not item.get("resolved")
        ]
        if unresolved_blocking:
            blocking_messages = "; ".join([f"{b['id']}: {b['message']}" for b in unresolved_blocking])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit PR: Unresolved blocking attention items present: {blocking_messages}"
            )

        # Guard 2: Basic completeness check
        if not pr_data.get("item_name") or not pr_data.get("quantity") or pr_data.get("quantity", 0) <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot submit PR: Requisition item name and positive quantity are required."
            )

        # Guard 3: Recommendation review status validation
        if rec_status == "rejected":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot submit PR: Demand recommendation was rejected. Please revise requirements and obtain an accepted or modified recommendation before submitting."
            )
        elif rec_status not in ["accepted", "modified", "kept_original"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit PR: Recommendation status is '{rec_status}'. You must review and accept or modify the recommendation before submitting."
            )

        # Guard 4: Prevent duplicate submission
        if pr_data.get("status") == "submitted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit PR: Requisition {pr_data.get('pr_number', '')} has already been submitted."
            )

        # Generate official PR Number if not yet set
        pr_number = pr_data.get("pr_number")
        if not pr_number:
            now = datetime.datetime.utcnow()
            pr_number = f"PR-{now.year}-{now.month:02d}-{uuid.uuid4().hex[:6].upper()}"
            pr_data["pr_number"] = pr_number

        submitted_at = datetime.datetime.utcnow().isoformat()
        pr_data["status"] = "submitted"
        pr_data["submitted_at"] = submitted_at

        progress_data["ready_for_submission"] = "complete"

        notes_suffix = f" (Notes: {payload.notes})" if payload and payload.notes else ""
        patch = {
            "pr": pr_data,
            "progress": progress_data,
            "messages": [
                AIMessage(
                    content=f"🎉 **Purchase Requisition {pr_number} Submitted Successfully!**\n\n"
                            f"Your PR for {pr_data.get('quantity')}x {pr_data.get('item_name')} "
                            f"has been officially logged into the ERP approval queue.{notes_suffix}"
                )
            ]
        }
        await graph.aupdate_state(config, patch)

        return SubmitPRResponse(
            thread_id=id,
            pr_number=pr_number,
            status="submitted",
            submitted_at=submitted_at,
            message=f"Purchase Requisition {pr_number} successfully submitted.",
            pr=pr_data,
            progress=progress_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting PR for thread {id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit purchase requisition for thread {id}"
        )

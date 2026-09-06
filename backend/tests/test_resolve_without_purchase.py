import copy

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from main import app
from app.api.v1.requests import (
    get_request_state,
    handle_recommendation_action,
    resolve_without_purchase,
    submit_purchase_requisition,
)
from app.schemas.requests import RecommendationActionRequest
from app.schemas.user_context import UserContext


class Snapshot:
    def __init__(self, values):
        self.values = values


class StatefulFakeGraph:
    """Small reducer-aware graph double for deterministic endpoint state tests."""

    def __init__(self, values):
        self.values = values

    async def aget_state(self, _config):
        return Snapshot(self.values)

    async def aupdate_state(self, _config, patch):
        merged = {**self.values}
        for key, value in patch.items():
            if key in {"pr", "demand", "progress"}:
                merged[key] = {**self.values.get(key, {}), **value}
            elif key == "messages":
                merged[key] = [*self.values.get(key, []), *value]
            else:
                merged[key] = value
        self.values = merged


USER = UserContext(user_id="usr_resolution_test")


def make_state(
    *,
    pr_quantity=0,
    demand_quantity=0,
    recommendation_status="accepted",
    attention_items=None,
    include_outcome=True,
):
    state = {
        "pr": {
            "item_name": "4K Monitor",
            "quantity": pr_quantity,
            "status": "draft",
            "specifications": [],
        },
        "demand": {
            "requested_qty": 5,
            "existing_inventory": 2,
            "assignable_assets": 3,
            "reserved_qty": 0,
            "net_new_purchase": demand_quantity,
            "estimated_saving": 2_500.0,
            "justification": "Internal stock and assignable assets fully cover the request.",
            "is_manually_overridden": False,
            "override_reason": None,
        },
        "progress": {
            "clarification": "complete",
            "demand_analysis": "complete",
            "validation": "complete",
            "ready_for_submission": "in_progress",
        },
        "attention_items": attention_items or [],
        "recommendation_status": recommendation_status,
        "messages": [],
        "agent_activity": [],
        "next_agent": "GeneratePR",
    }
    if include_outcome:
        state.update(
            {
                "request_outcome": "open",
                "resolution_provenance": None,
                "resolution_reason": None,
                "resolved_at": None,
            }
        )
    return state


async def call_with_graph(graph, endpoint, *args):
    with patch(
        "app.api.v1.requests.get_compiled_procure_graph",
        new=AsyncMock(return_value=graph),
    ):
        return await endpoint(*args)


@pytest.mark.asyncio
async def test_accept_zero_resolves_with_demand_analysis_provenance():
    graph = StatefulFakeGraph(make_state())

    result = await call_with_graph(
        graph, resolve_without_purchase, "thread_accept_zero", USER
    )

    assert result.request_outcome == "resolved_without_purchase"
    assert result.resolution_provenance == "demand_analysis"
    assert result.resolution_reason == graph.values["demand"]["justification"]
    assert result.pr["quantity"] == 0
    assert result.pr["status"] == "not_required"
    assert result.progress["ready_for_submission"] == "not_required"
    assert "pr_number" not in result.model_dump()
    assert not result.pr.get("pr_number")


@pytest.mark.asyncio
async def test_monitor_flow_accepts_zero_and_resolves_through_http_endpoint():
    thread_id = "thread_monitor_zero_e2e"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        chat_response = await client.post(
            "/api/v1/chat",
            json={
                "thread_id": thread_id,
                "message": "I need 5 4K monitors for the design team before September 1",
            },
        )
        assert chat_response.status_code == 200

        confirm_response = await client.post(
            f"/api/v1/requests/{thread_id}/confirm-specifications"
        )
        assert confirm_response.status_code == 200

        state = (
            await client.get(f"/api/v1/requests/{thread_id}/state")
        ).json()
        assert state["demand"]["requested_qty"] == 5
        assert state["demand"]["net_new_purchase"] == 0

        accept_response = await client.post(
            f"/api/v1/requests/{thread_id}/recommendation",
            json={"action": "accept"},
        )
        assert accept_response.status_code == 200
        assert accept_response.json()["pr"]["quantity"] == 0

        resolution_response = await client.post(
            f"/api/v1/requests/{thread_id}/resolve-without-purchase",
            json={},
        )
        assert resolution_response.status_code == 200
        data = resolution_response.json()
        assert data["request_outcome"] == "resolved_without_purchase"
        assert data["resolution_provenance"] == "demand_analysis"
        assert data["pr"]["status"] == "not_required"
        assert data["progress"]["ready_for_submission"] == "not_required"
        assert "pr_number" not in data


@pytest.mark.asyncio
async def test_modify_zero_requires_notes_and_records_user_override():
    missing_notes_graph = StatefulFakeGraph(
        make_state(pr_quantity=5, demand_quantity=2, recommendation_status="pending_review")
    )
    empty_notes_payload = RecommendationActionRequest.model_validate(
        {
            "action": "modify",
            "modification": {"net_new_purchase": 0, "user_notes": "   "},
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        await call_with_graph(
            missing_notes_graph,
            handle_recommendation_action,
            "thread_modify_zero_missing_notes",
            empty_notes_payload,
            USER,
        )
    assert exc_info.value.status_code == 400
    assert "notes are required" in exc_info.value.detail.lower()

    graph = StatefulFakeGraph(
        make_state(pr_quantity=5, demand_quantity=2, recommendation_status="pending_review")
    )
    notes = "Requester confirmed that the project will reuse existing displays"
    payload = RecommendationActionRequest.model_validate(
        {
            "action": "modify",
            "modification": {"net_new_purchase": 0, "user_notes": notes},
        }
    )
    await call_with_graph(
        graph, handle_recommendation_action, "thread_modify_zero", payload, USER
    )
    result = await call_with_graph(
        graph, resolve_without_purchase, "thread_modify_zero", USER
    )

    assert result.recommendation_status == "modified"
    assert result.resolution_provenance == "user_override"
    assert result.resolution_reason == notes


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("pr_quantity", "demand_quantity"),
    [(1, 0), (0, 1)],
)
async def test_resolve_rejects_quantity_mismatch_without_mutating_state(
    pr_quantity, demand_quantity
):
    initial = make_state(
        pr_quantity=pr_quantity, demand_quantity=demand_quantity
    )
    graph = StatefulFakeGraph(copy.deepcopy(initial))

    with pytest.raises(HTTPException) as exc_info:
        await call_with_graph(
            graph, resolve_without_purchase, "thread_mismatch", USER
        )

    assert exc_info.value.status_code == 400
    assert f"PR quantity is {pr_quantity}" in exc_info.value.detail
    assert f"net new purchase quantity is {demand_quantity}" in exc_info.value.detail
    assert graph.values == initial


@pytest.mark.asyncio
async def test_blocking_attention_prevents_resolution_but_warning_and_resolved_items_do_not():
    blocking_item = {
        "id": "spec_monitor_compatibility",
        "category": "specification",
        "severity": "blocking",
        "message": "Confirm that existing monitors meet the required specification.",
        "resolved": False,
    }
    graph = StatefulFakeGraph(make_state(attention_items=[blocking_item]))

    with pytest.raises(HTTPException) as exc_info:
        await call_with_graph(
            graph, resolve_without_purchase, "thread_blocking", USER
        )
    assert exc_info.value.status_code == 400
    assert "unresolved blocking" in exc_info.value.detail.lower()

    graph.values["attention_items"][0]["resolved"] = True
    resolved_result = await call_with_graph(
        graph, resolve_without_purchase, "thread_blocking", USER
    )
    assert resolved_result.request_outcome == "resolved_without_purchase"

    warning_item = {**blocking_item, "id": "policy_warning", "severity": "warning"}
    warning_graph = StatefulFakeGraph(make_state(attention_items=[warning_item]))
    warning_result = await call_with_graph(
        warning_graph, resolve_without_purchase, "thread_warning", USER
    )
    assert warning_result.request_outcome == "resolved_without_purchase"


@pytest.mark.asyncio
async def test_duplicate_resolution_is_rejected_without_duplicate_message():
    graph = StatefulFakeGraph(make_state())
    await call_with_graph(graph, resolve_without_purchase, "thread_duplicate", USER)
    message_count = len(graph.values["messages"])

    with pytest.raises(HTTPException) as exc_info:
        await call_with_graph(
            graph, resolve_without_purchase, "thread_duplicate", USER
        )

    assert exc_info.value.status_code == 400
    assert "already finalized" in exc_info.value.detail.lower()
    assert len(graph.values["messages"]) == message_count == 1


@pytest.mark.asyncio
async def test_submit_and_no_purchase_resolution_are_mutually_exclusive():
    resolved_graph = StatefulFakeGraph(make_state())
    await call_with_graph(
        resolved_graph, resolve_without_purchase, "thread_resolved_first", USER
    )
    with pytest.raises(HTTPException) as submit_exc:
        await call_with_graph(
            resolved_graph,
            submit_purchase_requisition,
            "thread_resolved_first",
            None,
            USER,
        )
    assert submit_exc.value.status_code == 400
    assert "resolved without purchase" in submit_exc.value.detail.lower()

    submitted_graph = StatefulFakeGraph(
        make_state(pr_quantity=2, demand_quantity=2)
    )
    await call_with_graph(
        submitted_graph,
        submit_purchase_requisition,
        "thread_submitted_first",
        None,
        USER,
    )
    with pytest.raises(HTTPException) as resolve_exc:
        await call_with_graph(
            submitted_graph,
            resolve_without_purchase,
            "thread_submitted_first",
            USER,
        )
    assert resolve_exc.value.status_code == 400
    assert "already finalized" in resolve_exc.value.detail.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("recommendation_status", ["none", "pending_review", "rejected"])
async def test_resolution_requires_valid_recommendation_status(recommendation_status):
    graph = StatefulFakeGraph(
        make_state(recommendation_status=recommendation_status)
    )

    with pytest.raises(HTTPException) as exc_info:
        await call_with_graph(
            graph, resolve_without_purchase, "thread_bad_status", USER
        )

    assert exc_info.value.status_code == 400
    assert "recommendation status" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_modified_zero_without_override_reason_is_rejected():
    state = make_state(recommendation_status="modified")
    state["demand"]["is_manually_overridden"] = True
    state["demand"]["override_reason"] = None
    graph = StatefulFakeGraph(state)

    with pytest.raises(HTTPException) as exc_info:
        await call_with_graph(
            graph, resolve_without_purchase, "thread_missing_override_reason", USER
        )

    assert exc_info.value.status_code == 400
    assert "override reason" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_positive_quantity_submit_still_succeeds_and_records_outcome():
    graph = StatefulFakeGraph(make_state(pr_quantity=2, demand_quantity=2))

    result = await call_with_graph(
        graph, submit_purchase_requisition, "thread_positive_submit", None, USER
    )

    assert result.status == "submitted"
    assert result.pr_number.startswith("PR-")
    assert result.pr["quantity"] == 2
    assert result.request_outcome == "purchase_submitted"
    assert graph.values["request_outcome"] == "purchase_submitted"


@pytest.mark.asyncio
async def test_legacy_positive_state_without_outcome_can_still_submit():
    graph = StatefulFakeGraph(
        make_state(pr_quantity=2, demand_quantity=2, include_outcome=False)
    )

    result = await call_with_graph(
        graph, submit_purchase_requisition, "thread_legacy_submit", None, USER
    )

    assert result.status == "submitted"
    assert graph.values["request_outcome"] == "purchase_submitted"


@pytest.mark.asyncio
async def test_legacy_zero_state_without_outcome_can_still_resolve():
    state = make_state(include_outcome=False)
    state["demand"].pop("justification")
    graph = StatefulFakeGraph(state)

    result = await call_with_graph(
        graph, resolve_without_purchase, "thread_legacy_resolve", USER
    )

    assert result.request_outcome == "resolved_without_purchase"
    assert result.resolution_provenance == "demand_analysis"
    assert result.resolution_reason


@pytest.mark.asyncio
async def test_get_state_normalizes_missing_legacy_outcome_to_open():
    graph = StatefulFakeGraph(
        make_state(pr_quantity=2, demand_quantity=2, include_outcome=False)
    )

    result = await call_with_graph(
        graph, get_request_state, "thread_legacy_get_state", USER
    )

    assert result.request_outcome == "open"
    assert result.resolution_provenance is None
    assert result.resolution_reason is None
    assert result.resolved_at is None


@pytest.mark.asyncio
async def test_resolve_without_purchase_returns_404_for_missing_thread():
    graph = StatefulFakeGraph({})

    with pytest.raises(HTTPException) as exc_info:
        await call_with_graph(
            graph, resolve_without_purchase, "missing_thread", USER
        )

    assert exc_info.value.status_code == 404

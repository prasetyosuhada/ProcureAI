import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport
from main import app
from app.api.v1.requests import (
    get_request_state,
    handle_recommendation_action,
    resolve_without_purchase,
    submit_purchase_requisition,
)
from app.schemas.requests import RecommendationActionRequest
from app.schemas.user_context import UserContext

@pytest.mark.asyncio
async def test_get_request_state_new_and_populated():
    """Verify GET /api/v1/requests/{id}/state for both initial/empty and populated threads."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Non-existent thread -> returns clean default initial state
        res1 = await client.get("/api/v1/requests/fresh_thread_999/state")
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["thread_id"] == "fresh_thread_999"
        assert data1["progress"]["clarification"] == "in_progress"
        assert data1["pr"]["status"] == "draft"
        assert data1["demand"] is None
        assert data1["request_outcome"] == "open"
        assert data1["messages"] == []

        # 2. Populate thread with a chat message
        chat_res = await client.post(
            "/api/v1/chat",
            json={
                "thread_id": "thread_req_test_01",
                "message": "I need 10 laptops for backend development before Sept 1 with 32GB RAM"
            }
        )
        assert chat_res.status_code == 200

        # 3. Retrieve populated state
        res2 = await client.get("/api/v1/requests/thread_req_test_01/state")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["thread_id"] == "thread_req_test_01"
        assert data2["pr"]["item_name"] == "Laptop"
        assert data2["pr"]["quantity"] == 10
        assert data2["progress"]["clarification"] == "in_progress"
        assert len(data2["agent_activity"]) >= 1


@pytest.mark.asyncio
async def test_confirm_specifications_endpoint():
    """Verify POST /api/v1/requests/{id}/confirm-specifications behavior for incomplete vs complete requirements."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Incomplete requirement -> Confirm fails with feedback
        thread_inc = "thread_confirm_inc_02"
        await client.post(
            "/api/v1/chat",
            json={"thread_id": thread_inc, "message": "I need laptops"}
        )

        res_inc = await client.post(f"/api/v1/requests/{thread_inc}/confirm-specifications")
        assert res_inc.status_code == 200
        data_inc = res_inc.json()
        assert data_inc["is_confirmed"] is False
        assert data_inc["next_agent"] == "Clarification"
        assert "cannot confirm" in data_inc["message"].lower() or "missing" in data_inc["message"].lower()

        # 2. Complete requirement -> Confirm succeeds, moves to Demand
        thread_comp = "thread_confirm_comp_03"
        await client.post(
            "/api/v1/chat",
            json={
                "thread_id": thread_comp,
                "message": "I need 10 laptops for backend development before Sept 1 with 32GB RAM"
            }
        )

        res_comp = await client.post(f"/api/v1/requests/{thread_comp}/confirm-specifications")
        assert res_comp.status_code == 200
        data_comp = res_comp.json()
        assert data_comp["is_confirmed"] is True
        assert data_comp["next_agent"] == "GeneratePR" or data_comp["progress"]["clarification"] == "complete"


@pytest.mark.asyncio
async def test_recommendation_action_modify():
    """Verify POST /api/v1/requests/{id}/recommendation with action='modify' (Option A - Pure State Mutation)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        thread_id = "thread_rec_modify_04"
        # Populate requirement & trigger demand analysis
        await client.post(
            "/api/v1/chat",
            json={
                "thread_id": thread_id,
                "message": "I need 10 laptops for backend development before Sept 1"
            }
        )
        await client.post(f"/api/v1/requests/{thread_id}/confirm-specifications")

        # Check state has demand (Requested: 10 - Stock: 3 - Assets: 5 = 2)
        s1 = (await client.get(f"/api/v1/requests/{thread_id}/state")).json()
        assert s1["demand"] is not None
        assert s1["demand"]["net_new_purchase"] == 2  # Deterministic calculation: 10 - 8 = 2

        # User modifies recommendation to 8 with justification notes
        mod_res = await client.post(
            f"/api/v1/requests/{thread_id}/recommendation",
            json={
                "action": "modify",
                "modification": {
                    "net_new_purchase": 8,
                    "user_notes": "Extra buffer for Q3 contractor cohort"
                }
            }
        )
        assert mod_res.status_code == 200
        data = mod_res.json()
        assert data["demand"]["net_new_purchase"] == 8
        assert data["demand"]["is_manually_overridden"] is True
        assert data["demand"]["override_reason"] == "Extra buffer for Q3 contractor cohort"
        assert data["pr"]["quantity"] == 8
        assert data["recommendation_status"] == "modified"
        assert data["progress"]["validation"] == "complete"


@pytest.mark.asyncio
async def test_recommendation_accept_promotes_net_new_purchase_to_final_pr_quantity():
    """Accept is the explicit point where the recommended quantity becomes final PR quantity."""

    class Snapshot:
        def __init__(self, values):
            self.values = values

    class FakeGraph:
        def __init__(self):
            self.values = {
                "pr": {"item_name": "Laptop", "quantity": 10, "status": "draft"},
                "demand": {"requested_qty": 10, "net_new_purchase": 2},
                "progress": {"validation": "in_progress"},
                "recommendation_status": "pending_review",
                "messages": [],
            }

        async def aget_state(self, _config):
            return Snapshot(self.values)

        async def aupdate_state(self, _config, patch):
            self.values = {
                **self.values,
                **patch,
                "pr": {**self.values.get("pr", {}), **patch.get("pr", {})},
                "progress": {**self.values.get("progress", {}), **patch.get("progress", {})},
            }

    graph = FakeGraph()
    with patch("app.api.v1.requests.get_compiled_procure_graph", new=AsyncMock(return_value=graph)):
        result = await handle_recommendation_action(
            "thread_accept_unit",
            RecommendationActionRequest(action="accept"),
            UserContext(user_id="usr_101"),
        )

    assert result.pr["quantity"] == 2
    assert graph.values["pr"]["quantity"] == 2


@pytest.mark.asyncio
async def test_recommendation_reject_restores_requested_quantity_and_blocks_pr():
    """Reject cancels the recommendation and leaves the PR at the original request quantity."""

    class Snapshot:
        def __init__(self, values):
            self.values = values

    class FakeGraph:
        def __init__(self):
            self.values = {
                "pr": {"item_name": "Laptop", "quantity": 8, "status": "draft"},
                "demand": {"requested_qty": 10, "net_new_purchase": 8},
                "progress": {"validation": "in_progress", "ready_for_submission": "pending"},
                "recommendation_status": "pending_review",
                "messages": [],
            }

        async def aget_state(self, _config):
            return Snapshot(self.values)

        async def aupdate_state(self, _config, patch):
            self.values = {
                **self.values,
                **patch,
                "pr": {**self.values.get("pr", {}), **patch.get("pr", {})},
                "progress": {**self.values.get("progress", {}), **patch.get("progress", {})},
            }

    graph = FakeGraph()
    with patch("app.api.v1.requests.get_compiled_procure_graph", new=AsyncMock(return_value=graph)):
        result = await handle_recommendation_action(
            "thread_reject_unit",
            RecommendationActionRequest(action="reject"),
            UserContext(user_id="usr_101"),
        )

    assert result.pr["quantity"] == 10
    assert result.pr["status"] == "rejected"
    assert result.recommendation_status == "rejected"
    assert result.request_outcome == "rejected"
    assert result.progress["validation"] == "blocked"
    assert result.progress["ready_for_submission"] == "blocked"


@pytest.mark.asyncio
async def test_recommendation_keep_original_is_explicit_and_submit_ready():
    """Keep Original retains requested quantity and records a distinct status."""

    class Snapshot:
        def __init__(self, values):
            self.values = values

    class FakeGraph:
        def __init__(self):
            self.values = {
                "pr": {"item_name": "Laptop", "quantity": 2, "status": "draft"},
                "demand": {"requested_qty": 10, "net_new_purchase": 2},
                "progress": {"validation": "in_progress", "ready_for_submission": "pending"},
                "recommendation_status": "pending_review",
                "messages": [],
            }

        async def aget_state(self, _config):
            return Snapshot(self.values)

        async def aupdate_state(self, _config, patch):
            self.values = {
                **self.values,
                **patch,
                "pr": {**self.values.get("pr", {}), **patch.get("pr", {})},
                "demand": {**self.values.get("demand", {}), **patch.get("demand", {})},
                "progress": {**self.values.get("progress", {}), **patch.get("progress", {})},
            }

    graph = FakeGraph()
    with patch("app.api.v1.requests.get_compiled_procure_graph", new=AsyncMock(return_value=graph)):
        result = await handle_recommendation_action(
            "thread_keep_original_unit",
            RecommendationActionRequest(action="keep_original"),
            UserContext(user_id="usr_101"),
        )

    assert result.pr["quantity"] == 10
    assert result.demand["net_new_purchase"] == 10
    assert result.demand["override_reason"] == "User chose to keep original requested quantity"
    assert result.recommendation_status == "kept_original"
    assert result.progress["validation"] == "complete"
    assert result.progress["ready_for_submission"] == "in_progress"


@pytest.mark.asyncio
async def test_recommendation_action_accept_and_reject():
    """Verify recommendation accept and reject actions."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        thread_accept = "thread_rec_accept_05"
        await client.post(
            "/api/v1/chat",
            json={"thread_id": thread_accept, "message": "I need 10 laptops for backend team before Sept 1"}
        )
        await client.post(f"/api/v1/requests/{thread_accept}/confirm-specifications")

        # Accept
        acc_res = await client.post(
            f"/api/v1/requests/{thread_accept}/recommendation",
            json={"action": "accept"}
        )
        assert acc_res.status_code == 200
        assert acc_res.json()["recommendation_status"] == "accepted"
        assert acc_res.json()["progress"]["validation"] == "complete"
        assert acc_res.json()["pr"]["quantity"] == 2

        # Reject
        thread_reject = "thread_rec_reject_06"
        await client.post(
            "/api/v1/chat",
            json={"thread_id": thread_reject, "message": "I need 10 laptops for backend team before Sept 1"}
        )
        await client.post(f"/api/v1/requests/{thread_reject}/confirm-specifications")

        rej_res = await client.post(
            f"/api/v1/requests/{thread_reject}/recommendation",
            json={"action": "reject"}
        )
        assert rej_res.status_code == 200
        assert rej_res.json()["recommendation_status"] == "rejected"
        assert rej_res.json()["progress"]["validation"] == "blocked"


@pytest.mark.asyncio
async def test_resolve_attention_item():
    """Verify POST /api/v1/requests/{id}/attention/{item_id}/resolve marks item resolved."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        thread_id = "thread_att_resolve_07"
        await client.post(
            "/api/v1/chat",
            json={
                "thread_id": thread_id,
                "message": "I need 10 laptops with RTX 4090 GPU for backend team before Sept 1"
            }
        )

        state = (await client.get(f"/api/v1/requests/{thread_id}/state")).json()
        assert len(state["attention_items"]) >= 1
        target_id = state["attention_items"][0]["id"]

        # Resolve attention item
        res = await client.post(f"/api/v1/requests/{thread_id}/attention/{target_id}/resolve")
        assert res.status_code == 200
        data = res.json()
        assert data["resolved_item_id"] == target_id

        # Verify state reflects resolved=True
        updated_state = (await client.get(f"/api/v1/requests/{thread_id}/state")).json()
        resolved_item = next(i for i in updated_state["attention_items"] if i["id"] == target_id)
        assert resolved_item["resolved"] is True


@pytest.mark.asyncio
async def test_submit_pr_with_guards():
    """Verify POST /api/v1/requests/{id}/submit validates blocking items and succeeds when valid."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        thread_id = "thread_submit_08"
        await client.post(
            "/api/v1/chat",
            json={
                "thread_id": thread_id,
                "message": "I need 10 laptops for backend team before Sept 1"
            }
        )
        await client.post(f"/api/v1/requests/{thread_id}/confirm-specifications")
        await client.post(
            f"/api/v1/requests/{thread_id}/recommendation",
            json={"action": "accept"}
        )

        # Submit PR
        sub_res = await client.post(
            f"/api/v1/requests/{thread_id}/submit",
            json={"notes": "Approved by Engineering Lead"}
        )
        assert sub_res.status_code == 200
        data = sub_res.json()
        assert data["status"] == "submitted"
        assert data["pr_number"].startswith("PR-")
        assert data["progress"]["ready_for_submission"] == "complete"
        assert data["pr"]["status"] == "submitted"
        assert data["pr"]["quantity"] == 2
        assert data["request_outcome"] == "purchase_submitted"


# ==============================================================================
# Out-of-Order Guard Test Cases
# ==============================================================================

@pytest.mark.asyncio
async def test_recommendation_rejected_before_demand_analysis():
    """Verify calling /recommendation fails with 400 when demand analysis has not been executed yet."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        thread_id = "thread_guard_rec_no_demand_09"
        # Only in clarification stage, demand is None
        await client.post(
            "/api/v1/chat",
            json={"thread_id": thread_id, "message": "I need laptops"}
        )

        res = await client.post(
            f"/api/v1/requests/{thread_id}/recommendation",
            json={"action": "accept"}
        )
        assert res.status_code == 400
        assert "No demand analysis available yet" in res.json()["detail"]


@pytest.mark.asyncio
async def test_submit_blocked_after_reject():
    """Verify /submit is rejected with 400 when recommendation was rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        thread_id = "thread_guard_submit_rejected_10"
        # Progress to demand analysis
        await client.post(
            "/api/v1/chat",
            json={"thread_id": thread_id, "message": "I need 10 laptops for backend team before Sept 1"}
        )
        await client.post(f"/api/v1/requests/{thread_id}/confirm-specifications")

        # Reject recommendation
        rej_res = await client.post(
            f"/api/v1/requests/{thread_id}/recommendation",
            json={"action": "reject"}
        )
        assert rej_res.status_code == 200

        # Attempt to submit -> must be blocked
        sub_res = await client.post(f"/api/v1/requests/{thread_id}/submit")
        assert sub_res.status_code == 400
        assert "rejected" in sub_res.json()["detail"].lower()

        # Check state: status is not submitted
        state = (await client.get(f"/api/v1/requests/{thread_id}/state")).json()
        assert state["pr"]["status"] != "submitted"


@pytest.mark.asyncio
async def test_submit_blocked_without_recommendation():
    """Verify /submit is blocked with 400 when recommendation_status is 'none'."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        thread_id = "thread_guard_submit_no_rec_11"
        # Progress through clarification and demand analysis, but do NOT call /recommendation
        await client.post(
            "/api/v1/chat",
            json={"thread_id": thread_id, "message": "I need 10 laptops for backend team before Sept 1"}
        )
        await client.post(f"/api/v1/requests/{thread_id}/confirm-specifications")

        # Attempt to submit directly without accepting/modifying recommendation
        sub_res = await client.post(f"/api/v1/requests/{thread_id}/submit")
        assert sub_res.status_code == 400
        assert "recommendation status" in sub_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_modify_rejects_negative_quantity():
    """Verify /recommendation rejects negative net_new_purchase quantities."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        thread_id = "thread_guard_rec_neg_12"
        await client.post(
            "/api/v1/chat",
            json={"thread_id": thread_id, "message": "I need 10 laptops for backend team before Sept 1"}
        )
        await client.post(f"/api/v1/requests/{thread_id}/confirm-specifications")

        # Attempt to modify with negative quantity
        mod_res = await client.post(
            f"/api/v1/requests/{thread_id}/recommendation",
            json={
                "action": "modify",
                "modification": {
                    "net_new_purchase": -5,
                    "user_notes": "Invalid negative qty"
                }
            }
        )
        # Should be rejected with 422 (Unprocessable Entity from Pydantic ge=0) or 400 (Bad Request from guard)
        assert mod_res.status_code in [400, 422]

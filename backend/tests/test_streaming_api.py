import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from main import app
from app.agent.activity import run_with_activity


def parse_sse(body: str):
    events = []
    for frame in body.split("\n\n"):
        data_lines = [line[6:] for line in frame.splitlines() if line.startswith("data: ")]
        if data_lines:
            events.append(json.loads("\n".join(data_lines)))
    return events


class ActivityTestState(TypedDict):
    value: int


@pytest.mark.asyncio
async def test_failed_operation_emits_running_then_failed():
    async def failing_node(_state: ActivityTestState):
        def fail():
            raise RuntimeError("private internal failure")

        await run_with_activity(
            "test.failure",
            "test_tool",
            "Checking test dependency",
            fail,
            lambda _result: "not reached",
        )
        return {"value": 1}

    graph = (
        StateGraph(ActivityTestState)
        .add_node("failure", failing_node)
        .add_edge(START, "failure")
        .add_edge("failure", END)
        .compile()
    )
    activities = []
    with pytest.raises(RuntimeError, match="private internal failure"):
        async for part in graph.astream(
            {"value": 0}, stream_mode="custom", version="v2"
        ):
            activities.append(part["data"]["activity"])

    assert [activity["status"] for activity in activities] == [
        "running",
        "failed",
    ]
    assert "private" not in activities[-1]["result_summary"]


@pytest.mark.asyncio
async def test_chat_stream_emits_safe_activity_and_compatible_result():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat/stream",
            json={
                "thread_id": "thread_stream_chat",
                "message": "Need 5 monitors for UI designers before Sept 15",
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        events = parse_sse(response.text)
        activities = [event for event in events if event["type"] == "activity"]
        result = next(event for event in events if event["type"] == "result")

        extraction = [
            event for event in activities
            if event["activity"]["id"] == "clarification.extraction"
        ]
        assert [event["activity"]["status"] for event in extraction] == [
            "running",
            "done",
        ]
        assert result["data"]["thread_id"] == "thread_stream_chat"
        assert result["data"]["message"]["role"] == "assistant"
        assert result["data"]["requirement_draft"]["quantity"] == 5
        assert all(event["run_id"].startswith("run_") for event in events)
        assert "prompt" not in response.text.lower()
        assert "database_url" not in response.text.lower()

        state = (await client.get("/api/requests/thread_stream_chat/state")).json()
        assert "transient_activities" not in state
        assert all("id" not in action for action in state["agent_activity"])


@pytest.mark.asyncio
async def test_confirmation_stream_emits_demand_tools_and_normal_result():
    transport = ASGITransport(app=app)
    thread_id = "thread_stream_confirm"
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        initial = await client.post(
            "/api/chat",
            json={
                "thread_id": thread_id,
                "message": "Need 5 monitors for UI designers before Sept 15",
            },
        )
        assert initial.status_code == 200

        response = await client.post(
            f"/api/requests/{thread_id}/confirm-specifications/stream",
            json={},
        )
        events = parse_sse(response.text)
        activities = [event["activity"] for event in events if event["type"] == "activity"]
        result = next(event["data"] for event in events if event["type"] == "result")

        assert response.status_code == 200
        assert result["is_confirmed"] is True
        assert result["progress"]["demand_analysis"] == "complete"
        for activity_id in ("demand.inventory", "demand.assets"):
            statuses = [
                activity["status"]
                for activity in activities
                if activity["id"] == activity_id
            ]
            assert statuses == ["running", "done"]


class FailingStreamingGraph:
    async def astream(self, *_args, **_kwargs):
        raise RuntimeError("internal database password must not leak")
        yield


@pytest.mark.asyncio
async def test_stream_failure_is_sanitized_as_error_event():
    transport = ASGITransport(app=app)
    with patch(
        "app.api.v1.chat.get_compiled_procure_graph",
        new=AsyncMock(return_value=FailingStreamingGraph()),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/chat/stream",
                json={"thread_id": "thread_stream_failure", "message": "Need a monitor"},
            )

    events = parse_sse(response.text)
    assert response.status_code == 200
    assert events[-1]["type"] == "error"
    assert events[-1]["detail"] == "Failed to process chat request"
    assert "password" not in response.text.lower()

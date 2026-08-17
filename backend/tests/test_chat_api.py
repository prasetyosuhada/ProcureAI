import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_chat_endpoint_new_thread():
    """Verify POST /api/v1/chat generates a new thread_id and invokes Clarification node."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"message": "I need laptops for my team"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "thread_id" in data
        assert data["thread_id"].startswith("thread_")
        assert data["message"]["role"] == "assistant"
        assert data["requirement_draft"] is not None
        assert data["requirement_draft"]["item"] == "Laptop"
        assert data["requirement_draft"]["is_complete"] is False
        assert data["next_agent"] == "Clarification"

@pytest.mark.asyncio
async def test_chat_endpoint_multi_turn_with_checkpointer():
    """Verify multi-turn state persistence across requests using the same thread_id."""
    thread_id = "thread_multi_turn_test_101"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: Incomplete requirement
        res1 = await client.post(
            "/api/v1/chat",
            json={
                "thread_id": thread_id,
                "message": "I need laptops for development"
            }
        )
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["thread_id"] == thread_id
        assert data1["requirement_draft"]["item"] == "Laptop"
        assert data1["requirement_draft"]["is_complete"] is False

        # Turn 2: Provide complete details in same thread
        res2 = await client.post(
            "/api/v1/chat",
            json={
                "thread_id": thread_id,
                "message": "10 laptops for backend development before Sept 1 with 32GB RAM and 1TB SSD"
            }
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["thread_id"] == thread_id
        assert data2["requirement_draft"]["is_complete"] is True
        assert data2["requirement_draft"]["quantity"] == 10
        # Verify automatic transition to Demand analysis node
        assert data2["demand_analysis"] is not None
        assert data2["demand_analysis"]["is_complete"] is True
        assert data2["demand_analysis"]["recommended_quantity"] == 2
        assert data2["next_agent"] == "GeneratePR"

@pytest.mark.asyncio
async def test_chat_input_sanitization():
    """Verify raw user input with HTML/Script tags is safely sanitized."""
    raw_xss_message = "<script>alert('xss')</script> Need 5 chairs"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"message": raw_xss_message}
        )
        assert response.status_code == 200
        data = response.json()
        # Script tags must not execute or appear unescaped in state item
        assert "<script>" not in str(data["requirement_draft"].get("item", ""))

@pytest.mark.asyncio
async def test_chat_user_context_integration():
    """Verify user context headers pass through to state machine and demand tools."""
    headers = {
        "X-User-ID": "usr_777",
        "X-User-Name": "Bob Tester",
        "X-Department-ID": "DEPT-ENG",
        "X-Cost-Center": "CC-ENG-001"
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            headers=headers,
            json={"message": "Need 10 laptops for backend development before Sept 1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["demand_analysis"] is not None
        assert data["demand_analysis"]["is_complete"] is True

import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_chat_multi_turn_flow():
    """Verify multi-turn chat interaction from initial request to demand analysis via FastAPI chat endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: Incomplete request
        res1 = await client.post(
            "/api/v1/chat",
            json={"message": "I need some laptops"}
        )
        assert res1.status_code == 200
        data1 = res1.json()
        assert "thread_id" in data1
        thread_id = data1["thread_id"]
        assert data1["next_agent"] == "Clarification"
        assert data1["requirement_draft"]["is_complete"] is False

        # Turn 2: Provide missing details -> complete draft, pauses for confirmation
        res2 = await client.post(
            "/api/v1/chat",
            json={
                "thread_id": thread_id,
                "message": "I need 10 laptops for backend development before Sept 1"
            }
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["thread_id"] == thread_id
        assert data2["requirement_draft"]["is_complete"] is True
        assert data2["requirement_draft"]["quantity"] == 10
        assert data2["next_agent"] == "Clarification"

        # Turn 3: Explicit action confirm specifications via confirmation_action=True -> triggers Demand Analysis
        res3 = await client.post(
            "/api/v1/chat",
            json={
                "thread_id": thread_id,
                "message": "I confirm the specifications. Please proceed to demand analysis.",
                "confirmation_action": True
            }
        )
        assert res3.status_code == 200
        data3 = res3.json()
        assert data3["demand_analysis"] is not None
        assert data3["demand_analysis"]["is_complete"] is True
        assert data3["demand_analysis"]["recommended_quantity"] == 2
        assert data3["next_agent"] == "GeneratePR"

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
    """Verify user context headers pass through to state machine and demand tools upon confirmation."""
    headers = {
        "X-User-ID": "usr_777",
        "X-User-Name": "Bob Tester",
        "X-Department-ID": "DEPT-ENG",
        "X-Cost-Center": "CC-ENG-001"
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res1 = await client.post(
            "/api/v1/chat",
            headers=headers,
            json={"message": "Need 10 laptops for backend development before Sept 1"}
        )
        assert res1.status_code == 200
        data1 = res1.json()
        thread_id = data1["thread_id"]

        # Explicit action confirm to trigger demand analysis
        res2 = await client.post(
            "/api/v1/chat",
            headers=headers,
            json={
                "thread_id": thread_id,
                "message": "I confirm the specifications. Please proceed to demand analysis.",
                "confirmation_action": True
            }
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["demand_analysis"] is not None
        assert data2["demand_analysis"]["is_complete"] is True

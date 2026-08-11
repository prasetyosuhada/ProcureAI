import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_chat_endpoint_new_thread():
    """Verify POST /api/v1/chat generates a new thread_id and returns structured response."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"message": "I need 10 developer laptops for new engineering hires."}
        )
        assert response.status_code == 200
        data = response.json()
        assert "thread_id" in data
        assert data["thread_id"].startswith("thread_")
        assert data["message"]["role"] == "assistant"
        assert "ProcureAI" in data["message"]["content"]
        assert data["requirement_draft"] is not None
        assert data["requirement_draft"]["item"] == "Laptop"

@pytest.mark.asyncio
async def test_chat_endpoint_existing_thread():
    """Verify POST /api/v1/chat preserves existing thread_id."""
    existing_thread = "thread_custom_999"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={
                "thread_id": existing_thread,
                "message": "Specifications should be 32GB RAM."
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == existing_thread

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
        # Escaped string should not contain unescaped <script>
        assert "<script>" not in data["message"]["content"]
        assert "&lt;script&gt;" in data["message"]["content"]

@pytest.mark.asyncio
async def test_chat_user_context_integration():
    """Verify user context headers personalize chat endpoint."""
    headers = {
        "X-User-ID": "usr_777",
        "X-User-Name": "Bob Tester"
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            headers=headers,
            json={"message": "Need monitors"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Bob Tester" in data["message"]["content"]

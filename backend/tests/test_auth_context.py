import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    """Verify health check endpoint returns 200 OK."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_default_user_context():
    """Verify default demo UserContext is injected when headers are omitted."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "usr_demo_100"
        assert data["department_id"] == "DEPT-ENG"
        assert data["cost_center"] == "CC-ENG-001"

@pytest.mark.asyncio
async def test_custom_header_user_context():
    """Verify custom headers securely override UserContext values."""
    headers = {
        "X-User-ID": "usr_exec_999",
        "X-User-Name": "Alice Smith",
        "X-User-Email": "alice@company.com",
        "X-Department-ID": "DEPT-FINANCE",
        "X-Cost-Center": "CC-FIN-002",
        "X-User-Role": "approver"
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "usr_exec_999"
        assert data["user_name"] == "Alice Smith"
        assert data["email"] == "alice@company.com"
        assert data["department_id"] == "DEPT-FINANCE"
        assert data["cost_center"] == "CC-FIN-002"
        assert data["role"] == "approver"

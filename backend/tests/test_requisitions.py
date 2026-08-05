import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget


async def get_auth_token(async_client: AsyncClient, email: str = "requester@procure.ai") -> str:
    response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "password123"}
    )
    assert response.status_code == 200, f"Login failed for {email}: {response.text}"
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_requisition_success(async_client: AsyncClient, db_session: AsyncSession):
    token = await get_auth_token(async_client, "requester@procure.ai")
    headers = {"Authorization": f"Bearer {token}"}

    # Retrieve seeded budget from database
    budget_result = await db_session.execute(select(Budget).limit(1))
    seeded_budget = budget_result.scalars().first()
    assert seeded_budget is not None, "Seeded budget should exist in DB"

    payload = {
        "budget_id": str(seeded_budget.id),
        "justification": "Upgrading team workstations for performance testing",
        "line_items": [
            {
                "item_name": "Dell UltraSharp 27 Monitor",
                "category": "Hardware",
                "quantity": 2,
                "estimated_unit_price": 450.00
            },
            {
                "item_name": "Logitech MX Master 3S Mouse",
                "category": "Hardware",
                "quantity": 2,
                "estimated_unit_price": 100.00
            }
        ]
    }

    response = await async_client.post("/api/v1/requisitions", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["pr_number"].startswith("PR-")
    assert data["status"] == "APPROVAL_PENDING"
    assert data["total_amount"] == 1100.0 or data["total_amount"] == "1100.00"
    assert len(data["line_items"]) == 2

    # Fetch created PR by ID
    pr_id = data["id"]
    get_response = await async_client.get(f"/api/v1/requisitions/{pr_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == pr_id


@pytest.mark.asyncio
async def test_create_requisition_invalid_budget(async_client: AsyncClient):
    token = await get_auth_token(async_client, "requester@procure.ai")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "budget_id": str(uuid.uuid4()),
        "justification": "PR with fake budget",
        "line_items": [
            {
                "item_name": "Test Item",
                "category": "Office",
                "quantity": 1,
                "estimated_unit_price": 10.00
            }
        ]
    }

    response = await async_client.post("/api/v1/requisitions", json=payload, headers=headers)
    assert response.status_code == 404
    assert "Budget" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_requisition_forbidden_role(async_client: AsyncClient):
    # Procurement officer should not be allowed to submit a PR
    token = await get_auth_token(async_client, "officer@procure.ai")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "budget_id": str(uuid.uuid4()),
        "justification": "Unauthorized PR submission attempt",
        "line_items": [
            {
                "item_name": "Test Item",
                "category": "Office",
                "quantity": 1,
                "estimated_unit_price": 10.00
            }
        ]
    }

    response = await async_client.post("/api/v1/requisitions", json=payload, headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Operation not permitted for this role"


@pytest.mark.asyncio
async def test_list_requisitions(async_client: AsyncClient):
    token = await get_auth_token(async_client, "manager@procure.ai")
    headers = {"Authorization": f"Bearer {token}"}

    # List requisitions
    response = await async_client.get("/api/v1/requisitions", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Get non-existent requisition
    fake_id = str(uuid.uuid4())
    response_404 = await async_client.get(f"/api/v1/requisitions/{fake_id}", headers=headers)
    assert response_404.status_code == 404

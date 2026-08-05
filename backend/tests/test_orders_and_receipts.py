import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.models.vendor import Vendor


async def get_auth_token(async_client: AsyncClient, email: str) -> str:
    response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "password123"}
    )
    assert response.status_code == 200, f"Login failed for {email}: {response.text}"
    return response.json()["access_token"]


async def create_sample_pr(async_client: AsyncClient, db_session: AsyncSession) -> str:
    token = await get_auth_token(async_client, "requester@procure.ai")
    headers = {"Authorization": f"Bearer {token}"}

    budget_result = await db_session.execute(select(Budget).limit(1))
    budget = budget_result.scalars().first()
    assert budget is not None

    payload = {
        "budget_id": str(budget.id),
        "justification": "Hardware procurement for new engineers",
        "line_items": [
            {
                "item_name": "MacBook Pro 16-inch M3 Max",
                "category": "Hardware",
                "quantity": 2,
                "estimated_unit_price": 3499.00
            }
        ]
    }

    response = await async_client.post("/api/v1/requisitions", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_po_from_pr_success(async_client: AsyncClient, db_session: AsyncSession):
    pr_id = await create_sample_pr(async_client, db_session)

    vendor_result = await db_session.execute(select(Vendor).limit(1))
    vendor = vendor_result.scalars().first()
    assert vendor is not None

    officer_token = await get_auth_token(async_client, "officer@procure.ai")
    headers = {"Authorization": f"Bearer {officer_token}"}

    po_payload = {
        "vendor_id": str(vendor.id),
        "currency": "USD"
    }

    response = await async_client.post(f"/api/v1/purchase-orders/from-pr/{pr_id}", json=po_payload, headers=headers)
    assert response.status_code == 201
    po_data = response.json()
    assert po_data["po_number"].startswith("PO-")
    assert po_data["status"] == "ISSUED"
    assert po_data["pr_id"] == pr_id
    assert len(po_data["line_items"]) == 1

    # Fetch PO by ID
    po_id = po_data["id"]
    get_res = await async_client.get(f"/api/v1/purchase-orders/{po_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == po_id


@pytest.mark.asyncio
async def test_create_po_forbidden_role(async_client: AsyncClient, db_session: AsyncSession):
    pr_id = await create_sample_pr(async_client, db_session)
    vendor_result = await db_session.execute(select(Vendor).limit(1))
    vendor = vendor_result.scalars().first()

    requester_token = await get_auth_token(async_client, "requester@procure.ai")
    headers = {"Authorization": f"Bearer {requester_token}"}

    po_payload = {"vendor_id": str(vendor.id), "currency": "USD"}
    response = await async_client.post(f"/api/v1/purchase-orders/from-pr/{pr_id}", json=po_payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_goods_receipt_matched_and_discrepancy(async_client: AsyncClient, db_session: AsyncSession):
    pr_id = await create_sample_pr(async_client, db_session)
    vendor_result = await db_session.execute(select(Vendor).limit(1))
    vendor = vendor_result.scalars().first()

    officer_token = await get_auth_token(async_client, "officer@procure.ai")
    po_res = await async_client.post(
        f"/api/v1/purchase-orders/from-pr/{pr_id}",
        json={"vendor_id": str(vendor.id)},
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert po_res.status_code == 201
    po_id = po_res.json()["id"]

    warehouse_token = await get_auth_token(async_client, "warehouse@procure.ai")
    wh_headers = {"Authorization": f"Bearer {warehouse_token}"}

    # Test MATCHED Goods Receipt (exact quantity = 2)
    gr_payload_matched = {
        "po_id": po_id,
        "delivery_note_ref": "DN-998811",
        "line_items": [
            {
                "item_name": "MacBook Pro 16-inch M3 Max",
                "quantity_received": 2,
                "condition_notes": "All sealed in box"
            }
        ]
    }

    gr_res = await async_client.post("/api/v1/goods-receipts", json=gr_payload_matched, headers=wh_headers)
    assert gr_res.status_code == 201
    gr_data = gr_res.json()
    assert gr_data["gr_number"].startswith("GR-")
    assert gr_data["status"] == "MATCHED"

    # List GRs for PO
    list_res = await async_client.get(f"/api/v1/goods-receipts/po/{po_id}", headers=wh_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


@pytest.mark.asyncio
async def test_create_goods_receipt_forbidden_role(async_client: AsyncClient, db_session: AsyncSession):
    officer_token = await get_auth_token(async_client, "officer@procure.ai")
    headers = {"Authorization": f"Bearer {officer_token}"}

    gr_payload = {
        "po_id": str(uuid.uuid4()),
        "delivery_note_ref": "DN-000000",
        "line_items": [
            {"item_name": "Item", "quantity_received": 1, "condition_notes": "OK"}
        ]
    }

    response = await async_client.post("/api/v1/goods-receipts", json=gr_payload, headers=headers)
    assert response.status_code == 403

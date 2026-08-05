import uuid
from datetime import date
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


async def create_sample_po(async_client: AsyncClient, db_session: AsyncSession) -> tuple[str, str]:
    # 1. Fetch budget & vendor IDs up front before API calls expire session objects
    budget_res = await db_session.execute(select(Budget).limit(1))
    budget = budget_res.scalars().first()
    budget_id = str(budget.id)

    vendor_res = await db_session.execute(select(Vendor).limit(1))
    vendor = vendor_res.scalars().first()
    vendor_id = str(vendor.id)

    # 2. Create PR
    req_token = await get_auth_token(async_client, "requester@procure.ai")
    pr_res = await async_client.post(
        "/api/v1/requisitions",
        json={
            "budget_id": budget_id,
            "justification": "Software license renewal",
            "line_items": [
                {
                    "item_name": "JetBrains All Products Pack",
                    "category": "Software",
                    "quantity": 5,
                    "estimated_unit_price": 499.00
                }
            ]
        },
        headers={"Authorization": f"Bearer {req_token}"}
    )
    assert pr_res.status_code == 201
    pr_id = pr_res.json()["id"]

    # 3. Issue PO
    off_token = await get_auth_token(async_client, "officer@procure.ai")
    po_res = await async_client.post(
        f"/api/v1/purchase-orders/from-pr/{pr_id}",
        json={"vendor_id": vendor_id, "currency": "USD"},
        headers={"Authorization": f"Bearer {off_token}"}
    )
    assert po_res.status_code == 201
    po_id = po_res.json()["id"]

    return po_id, vendor_id


@pytest.mark.asyncio
async def test_submit_invoice_success(async_client: AsyncClient, db_session: AsyncSession):
    po_id, vendor_id = await create_sample_po(async_client, db_session)
    ap_token = await get_auth_token(async_client, "ap@procure.ai")
    headers = {"Authorization": f"Bearer {ap_token}"}

    invoice_payload = {
        "invoice_number": "INV-2026-0001",
        "po_id": po_id,
        "vendor_id": vendor_id,
        "invoice_date": str(date.today()),
        "total_amount": 2495.00,
        "tax_amount": 0.00,
        "line_items": [
            {
                "description": "JetBrains All Products Pack",
                "quantity": 5,
                "unit_price": 499.00,
                "total": 2495.00
            }
        ]
    }

    response = await async_client.post("/api/v1/invoices", json=invoice_payload, headers=headers)
    assert response.status_code == 201
    inv_data = response.json()
    assert inv_data["invoice_number"] == "INV-2026-0001"
    assert inv_data["status"] == "PENDING_MATCH"
    assert inv_data["po_id"] == po_id

    # Fetch Invoice by ID
    inv_id = inv_data["id"]
    get_res = await async_client.get(f"/api/v1/invoices/{inv_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == inv_id


@pytest.mark.asyncio
async def test_submit_duplicate_invoice_number(async_client: AsyncClient, db_session: AsyncSession):
    po_id, vendor_id = await create_sample_po(async_client, db_session)
    ap_token = await get_auth_token(async_client, "ap@procure.ai")
    headers = {"Authorization": f"Bearer {ap_token}"}

    invoice_payload = {
        "invoice_number": "INV-DUP-9999",
        "po_id": po_id,
        "vendor_id": vendor_id,
        "invoice_date": str(date.today()),
        "total_amount": 100.00,
        "tax_amount": 0.00,
        "line_items": [
            {
                "description": "Sample item",
                "quantity": 1,
                "unit_price": 100.00,
                "total": 100.00
            }
        ]
    }

    # First submission
    res1 = await async_client.post("/api/v1/invoices", json=invoice_payload, headers=headers)
    assert res1.status_code == 201

    # Second submission (duplicate)
    res2 = await async_client.post("/api/v1/invoices", json=invoice_payload, headers=headers)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_submit_invoice_forbidden_role(async_client: AsyncClient, db_session: AsyncSession):
    po_id, vendor_id = await create_sample_po(async_client, db_session)
    req_token = await get_auth_token(async_client, "requester@procure.ai")
    headers = {"Authorization": f"Bearer {req_token}"}

    invoice_payload = {
        "invoice_number": "INV-UNAUTH-01",
        "po_id": po_id,
        "vendor_id": vendor_id,
        "invoice_date": str(date.today()),
        "total_amount": 500.00,
        "tax_amount": 0.00,
        "line_items": [
            {
                "description": "Sample item",
                "quantity": 1,
                "unit_price": 500.00,
                "total": 500.00
            }
        ]
    }

    response = await async_client.post("/api/v1/invoices", json=invoice_payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_invoices(async_client: AsyncClient):
    token = await get_auth_token(async_client, "manager@procure.ai")
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get("/api/v1/invoices", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

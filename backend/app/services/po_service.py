from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import PurchaseOrder
from app.models.requisition import PurchaseRequisition
from app.models.vendor import Vendor
from app.repositories.order_repo import order_repo
from app.schemas.order import POCreateSchema


class POService:
    async def create_po_from_pr(
        self,
        session: AsyncSession,
        pr_id: UUID,
        po_data: POCreateSchema
    ) -> PurchaseOrder:
        # Verify PR exists
        pr_result = await session.execute(
            select(PurchaseRequisition).where(PurchaseRequisition.id == pr_id)
        )
        pr = pr_result.scalars().first()
        if not pr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase Requisition with ID '{pr_id}' not found."
            )

        # Verify Vendor exists
        vendor_result = await session.execute(
            select(Vendor).where(Vendor.id == po_data.vendor_id)
        )
        vendor = vendor_result.scalars().first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor with ID '{po_data.vendor_id}' not found."
            )

        # Build line items snapshot and calculate total amount
        line_items_dict = []
        total_amount = Decimal("0.00")

        if po_data.line_items:
            for item in po_data.line_items:
                line_total = Decimal(str(item.quantity)) * item.unit_price
                total_amount += line_total
                line_items_dict.append({
                    "item_name": item.item_name,
                    "category": item.category,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "total": float(line_total)
                })
        else:
            # Snapshot from PR line_items
            for item in pr.line_items:
                qty = int(item.get("quantity", 1))
                unit_price = Decimal(str(item.get("estimated_unit_price", "0.00")))
                line_total = Decimal(str(qty)) * unit_price
                total_amount += line_total
                line_items_dict.append({
                    "item_name": item.get("item_name", "Unknown Item"),
                    "category": item.get("category", "General"),
                    "quantity": qty,
                    "unit_price": float(unit_price),
                    "total": float(line_total)
                })

        po_number = await order_repo.generate_po_number(session)
        now = datetime.now(timezone.utc)

        po = PurchaseOrder(
            po_number=po_number,
            pr_id=pr_id,
            vendor_id=po_data.vendor_id,
            status="ISSUED",
            total_amount=total_amount,
            currency=po_data.currency,
            line_items=line_items_dict,
            issued_at=now,
            created_at=now
        )

        return await order_repo.create(session, po)

    async def get_po(self, session: AsyncSession, po_id: UUID) -> PurchaseOrder:
        po = await order_repo.get_by_id(session, po_id)
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase Order with ID '{po_id}' not found."
            )
        return po

    async def list_pos(
        self,
        session: AsyncSession,
        vendor_id: UUID | None = None,
        po_status: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[PurchaseOrder]:
        return await order_repo.list_all(
            session=session,
            vendor_id=vendor_id,
            status=po_status,
            skip=skip,
            limit=limit
        )


po_service = POService()

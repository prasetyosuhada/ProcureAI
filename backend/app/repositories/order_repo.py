from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import PurchaseOrder


class OrderRepository:
    async def create(self, session: AsyncSession, po: PurchaseOrder) -> PurchaseOrder:
        session.add(po)
        await session.commit()
        await session.refresh(po)
        return po

    async def get_by_id(self, session: AsyncSession, po_id: UUID) -> PurchaseOrder | None:
        result = await session.execute(
            select(PurchaseOrder).where(PurchaseOrder.id == po_id)
        )
        return result.scalars().first()

    async def get_by_number(self, session: AsyncSession, po_number: str) -> PurchaseOrder | None:
        result = await session.execute(
            select(PurchaseOrder).where(PurchaseOrder.po_number == po_number)
        )
        return result.scalars().first()

    async def list_all(
        self,
        session: AsyncSession,
        vendor_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[PurchaseOrder]:
        query = select(PurchaseOrder)
        if vendor_id:
            query = query.where(PurchaseOrder.vendor_id == vendor_id)
        if status:
            query = query.where(PurchaseOrder.status == status)
        query = query.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def generate_po_number(self, session: AsyncSession) -> str:
        current_year = datetime.now(timezone.utc).year
        prefix = f"PO-{current_year}-"
        result = await session.execute(
            select(func.count(PurchaseOrder.id)).where(
                PurchaseOrder.po_number.like(f"{prefix}%")
            )
        )
        count = result.scalar() or 0
        return f"{prefix}{count + 1:04d}"


order_repo = OrderRepository()

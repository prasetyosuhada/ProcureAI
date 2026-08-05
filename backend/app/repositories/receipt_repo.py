from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.receipt import GoodsReceipt


class ReceiptRepository:
    async def create(self, session: AsyncSession, gr: GoodsReceipt) -> GoodsReceipt:
        session.add(gr)
        await session.commit()
        await session.refresh(gr)
        return gr

    async def get_by_id(self, session: AsyncSession, gr_id: UUID) -> GoodsReceipt | None:
        result = await session.execute(
            select(GoodsReceipt).where(GoodsReceipt.id == gr_id)
        )
        return result.scalars().first()

    async def list_by_po(self, session: AsyncSession, po_id: UUID) -> list[GoodsReceipt]:
        result = await session.execute(
            select(GoodsReceipt)
            .where(GoodsReceipt.po_id == po_id)
            .order_by(GoodsReceipt.received_at.desc())
        )
        return list(result.scalars().all())

    async def generate_gr_number(self, session: AsyncSession) -> str:
        current_year = datetime.now(timezone.utc).year
        prefix = f"GR-{current_year}-"
        result = await session.execute(
            select(func.count(GoodsReceipt.id)).where(
                GoodsReceipt.gr_number.like(f"{prefix}%")
            )
        )
        count = result.scalar() or 0
        return f"{prefix}{count + 1:04d}"


receipt_repo = ReceiptRepository()

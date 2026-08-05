from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.invoice import Invoice


class InvoiceRepository:
    async def create(self, session: AsyncSession, invoice: Invoice) -> Invoice:
        session.add(invoice)
        await session.commit()
        await session.refresh(invoice)
        return invoice

    async def get_by_id(self, session: AsyncSession, invoice_id: UUID) -> Invoice | None:
        result = await session.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        return result.scalars().first()

    async def get_by_vendor_and_number(
        self,
        session: AsyncSession,
        vendor_id: UUID,
        invoice_number: str
    ) -> Invoice | None:
        result = await session.execute(
            select(Invoice).where(
                Invoice.vendor_id == vendor_id,
                Invoice.invoice_number == invoice_number
            )
        )
        return result.scalars().first()

    async def list_all(
        self,
        session: AsyncSession,
        po_id: UUID | None = None,
        vendor_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[Invoice]:
        query = select(Invoice)
        if po_id:
            query = query.where(Invoice.po_id == po_id)
        if vendor_id:
            query = query.where(Invoice.vendor_id == vendor_id)
        if status:
            query = query.where(Invoice.status == status)
        query = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())


invoice_repo = InvoiceRepository()

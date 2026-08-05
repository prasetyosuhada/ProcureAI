from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice
from app.models.vendor import Vendor
from app.repositories.invoice_repo import invoice_repo
from app.repositories.order_repo import order_repo
from app.schemas.invoice import InvoiceCreateSchema


class InvoiceService:
    async def create_invoice(
        self,
        session: AsyncSession,
        submitted_by_id: UUID,
        invoice_data: InvoiceCreateSchema
    ) -> Invoice:
        # Verify target PO exists
        po = await order_repo.get_by_id(session, invoice_data.po_id)
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase Order with ID '{invoice_data.po_id}' not found."
            )

        # Verify Vendor exists
        vendor_result = await session.execute(
            select(Vendor).where(Vendor.id == invoice_data.vendor_id)
        )
        vendor = vendor_result.scalars().first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor with ID '{invoice_data.vendor_id}' not found."
            )

        # Check for duplicate invoice number for the same vendor
        existing = await invoice_repo.get_by_vendor_and_number(
            session=session,
            vendor_id=invoice_data.vendor_id,
            invoice_number=invoice_data.invoice_number
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invoice number '{invoice_data.invoice_number}' already exists for this vendor."
            )

        formatted_line_items = [
            {
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "total": float(item.total)
            }
            for item in invoice_data.line_items
        ]

        now = datetime.now(timezone.utc)
        invoice = Invoice(
            invoice_number=invoice_data.invoice_number,
            po_id=invoice_data.po_id,
            vendor_id=invoice_data.vendor_id,
            submitted_by_id=submitted_by_id,
            invoice_date=invoice_data.invoice_date,
            total_amount=invoice_data.total_amount,
            tax_amount=invoice_data.tax_amount,
            line_items=formatted_line_items,
            status="PENDING_MATCH",
            created_at=now
        )

        return await invoice_repo.create(session, invoice)

    async def get_invoice(self, session: AsyncSession, invoice_id: UUID) -> Invoice:
        invoice = await invoice_repo.get_by_id(session, invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID '{invoice_id}' not found."
            )
        return invoice

    async def list_invoices(
        self,
        session: AsyncSession,
        po_id: UUID | None = None,
        vendor_id: UUID | None = None,
        invoice_status: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[Invoice]:
        return await invoice_repo.list_all(
            session=session,
            po_id=po_id,
            vendor_id=vendor_id,
            status=invoice_status,
            skip=skip,
            limit=limit
        )


invoice_service = InvoiceService()

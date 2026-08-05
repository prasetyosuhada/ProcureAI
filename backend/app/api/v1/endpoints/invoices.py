from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.invoice import InvoiceCreateSchema, InvoiceResponseSchema
from app.services.invoice_service import invoice_service

router = APIRouter()


@router.post("", response_model=InvoiceResponseSchema, status_code=status.HTTP_201_CREATED)
async def submit_invoice(
    invoice_data: InvoiceCreateSchema,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(RoleChecker(["AP_CLERK"]))]
):
    """
    Submit a vendor invoice for 3-way matching. Allowed roles: AP_CLERK.
    """
    return await invoice_service.create_invoice(
        session=session,
        submitted_by_id=current_user.id,
        invoice_data=invoice_data
    )


@router.get("", response_model=list[InvoiceResponseSchema])
async def list_invoices(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    po_id: UUID | None = Query(None, description="Filter by Purchase Order ID"),
    vendor_id: UUID | None = Query(None, description="Filter by Vendor ID"),
    invoice_status: str | None = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return")
):
    """
    List vendor invoices with optional filtering. Accessible by all authenticated users.
    """
    return await invoice_service.list_invoices(
        session=session,
        po_id=po_id,
        vendor_id=vendor_id,
        invoice_status=invoice_status,
        skip=skip,
        limit=limit
    )


@router.get("/{id}", response_model=InvoiceResponseSchema)
async def get_invoice(
    id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Get vendor invoice details by ID. Accessible by all authenticated users.
    """
    return await invoice_service.get_invoice(session=session, invoice_id=id)

from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.order import POCreateSchema, POResponseSchema
from app.services.po_service import po_service

router = APIRouter()


@router.post("/from-pr/{pr_id}", response_model=POResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_po_from_pr(
    pr_id: UUID,
    po_data: POCreateSchema,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(RoleChecker(["PROCUREMENT_OFFICER"]))]
):
    """
    Generate a Purchase Order from an existing Purchase Requisition. Allowed roles: PROCUREMENT_OFFICER.
    """
    return await po_service.create_po_from_pr(
        session=session,
        pr_id=pr_id,
        po_data=po_data
    )


@router.get("", response_model=list[POResponseSchema])
async def list_purchase_orders(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    vendor_id: UUID | None = Query(None, description="Filter by Vendor ID"),
    po_status: str | None = Query(None, alias="status", description="Filter by PO status"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return")
):
    """
    List Purchase Orders with optional filtering. Accessible by all authenticated users.
    """
    return await po_service.list_pos(
        session=session,
        vendor_id=vendor_id,
        po_status=po_status,
        skip=skip,
        limit=limit
    )


@router.get("/{id}", response_model=POResponseSchema)
async def get_purchase_order(
    id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Get Purchase Order details by ID. Accessible by all authenticated users.
    """
    return await po_service.get_po(session=session, po_id=id)

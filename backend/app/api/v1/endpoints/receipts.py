from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.receipt import GRCreateSchema, GRResponseSchema
from app.services.gr_service import gr_service

router = APIRouter()


@router.post("", response_model=GRResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_goods_receipt(
    gr_data: GRCreateSchema,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(RoleChecker(["WAREHOUSE_STAFF"]))]
):
    """
    Record a Goods Receipt against a Purchase Order. Allowed roles: WAREHOUSE_STAFF.
    """
    return await gr_service.create_goods_receipt(
        session=session,
        received_by_id=current_user.id,
        gr_data=gr_data
    )


@router.get("/po/{po_id}", response_model=list[GRResponseSchema])
async def list_goods_receipts_for_po(
    po_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    List all Goods Receipts associated with a specific Purchase Order. Accessible by all authenticated users.
    """
    return await gr_service.list_grs_for_po(session=session, po_id=po_id)

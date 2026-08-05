from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.requisition import PRCreateSchema, PRResponseSchema
from app.services.requisition_service import requisition_service

router = APIRouter()


@router.post("", response_model=PRResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_requisition(
    pr_data: PRCreateSchema,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(RoleChecker(["REQUESTER"]))]
):
    """
    Submit a new Purchase Requisition (PR). Only users with REQUESTER role are allowed.
    """
    return await requisition_service.create_requisition(
        session=session,
        requester_id=current_user.id,
        pr_data=pr_data
    )


@router.get("", response_model=list[PRResponseSchema])
async def list_requisitions(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pr_status: str | None = Query(None, alias="status", description="Filter by status"),
    requester_id: UUID | None = Query(None, description="Filter by requester ID"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return")
):
    """
    List Purchase Requisitions with optional filters. Accessible by all authenticated users.
    """
    return await requisition_service.list_requisitions(
        session=session,
        requester_id=requester_id,
        pr_status=pr_status,
        skip=skip,
        limit=limit
    )


@router.get("/{id}", response_model=PRResponseSchema)
async def get_requisition(
    id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Get detailed information of a Purchase Requisition by ID. Accessible by all authenticated users.
    """
    return await requisition_service.get_requisition(session=session, pr_id=id)

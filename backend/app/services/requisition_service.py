from decimal import Decimal
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.models.requisition import PurchaseRequisition
from app.repositories.requisition_repo import requisition_repo
from app.schemas.requisition import PRCreateSchema


class RequisitionService:
    async def create_requisition(
        self,
        session: AsyncSession,
        requester_id: UUID,
        pr_data: PRCreateSchema
    ) -> PurchaseRequisition:
        # Verify budget existence
        budget_result = await session.execute(
            select(Budget).where(Budget.id == pr_data.budget_id)
        )
        budget = budget_result.scalars().first()
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Budget with ID '{pr_data.budget_id}' not found."
            )

        # Calculate total amount & format line items for JSON storage
        total_amount = Decimal("0.00")
        line_items_dict = []
        for item in pr_data.line_items:
            item_total = Decimal(str(item.quantity)) * item.estimated_unit_price
            total_amount += item_total
            line_items_dict.append({
                "item_name": item.item_name,
                "category": item.category,
                "quantity": item.quantity,
                "estimated_unit_price": float(item.estimated_unit_price)
            })

        pr_number = await requisition_repo.generate_pr_number(session)

        pr = PurchaseRequisition(
            pr_number=pr_number,
            requester_id=requester_id,
            budget_id=pr_data.budget_id,
            status="APPROVAL_PENDING",
            justification=pr_data.justification,
            total_amount=total_amount,
            line_items=line_items_dict,
            validation_result=None
        )

        return await requisition_repo.create(session, pr)

    async def get_requisition(self, session: AsyncSession, pr_id: UUID) -> PurchaseRequisition:
        pr = await requisition_repo.get_by_id(session, pr_id)
        if not pr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase Requisition with ID '{pr_id}' not found."
            )
        return pr

    async def list_requisitions(
        self,
        session: AsyncSession,
        requester_id: UUID | None = None,
        pr_status: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[PurchaseRequisition]:
        return await requisition_repo.list_all(
            session=session,
            requester_id=requester_id,
            status=pr_status,
            skip=skip,
            limit=limit
        )


requisition_service = RequisitionService()

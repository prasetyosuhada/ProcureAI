from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.requisition import PurchaseRequisition


class RequisitionRepository:
    async def create(self, session: AsyncSession, pr: PurchaseRequisition) -> PurchaseRequisition:
        session.add(pr)
        await session.commit()
        await session.refresh(pr)
        return pr

    async def get_by_id(self, session: AsyncSession, pr_id: UUID) -> PurchaseRequisition | None:
        result = await session.execute(
            select(PurchaseRequisition).where(PurchaseRequisition.id == pr_id)
        )
        return result.scalars().first()

    async def get_by_number(self, session: AsyncSession, pr_number: str) -> PurchaseRequisition | None:
        result = await session.execute(
            select(PurchaseRequisition).where(PurchaseRequisition.pr_number == pr_number)
        )
        return result.scalars().first()

    async def list_all(
        self,
        session: AsyncSession,
        requester_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[PurchaseRequisition]:
        query = select(PurchaseRequisition)
        if requester_id:
            query = query.where(PurchaseRequisition.requester_id == requester_id)
        if status:
            query = query.where(PurchaseRequisition.status == status)
        query = query.order_by(PurchaseRequisition.created_at.desc()).offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def generate_pr_number(self, session: AsyncSession) -> str:
        current_year = datetime.now(timezone.utc).year
        prefix = f"PR-{current_year}-"
        result = await session.execute(
            select(func.count(PurchaseRequisition.id)).where(
                PurchaseRequisition.pr_number.like(f"{prefix}%")
            )
        )
        count = result.scalar() or 0
        return f"{prefix}{count + 1:04d}"


requisition_repo = RequisitionRepository()

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base

class PurchaseRequisition(Base):
    __tablename__ = "purchase_requisitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pr_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    requester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    budget_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("budgets.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    justification: Mapped[str] = mapped_column(String, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    line_items: Mapped[dict] = mapped_column(JSONB, nullable=False)
    validation_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

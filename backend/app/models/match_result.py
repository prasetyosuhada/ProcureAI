import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base

class MatchResult(Base):
    __tablename__ = "match_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), unique=True, nullable=False)
    po_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    overall_status: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    discrepancies: Mapped[dict] = mapped_column(JSONB, nullable=False, default=[])
    reasoning_summary: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    resolution_action: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

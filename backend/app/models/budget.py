import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base

class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    spent_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0.00)
    reserved_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0.00)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

import datetime
import uuid
from sqlalchemy import Column, String, Float, DateTime
from app.db.base import Base

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cost_center = Column(String, unique=True, index=True, nullable=False)
    department_name = Column(String, nullable=False)
    department_id = Column(String, index=True, nullable=True)
    allocated_budget = Column(Float, default=0.0, nullable=False)
    consumed_budget = Column(Float, default=0.0, nullable=False)
    remaining_budget = Column(Float, default=0.0, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

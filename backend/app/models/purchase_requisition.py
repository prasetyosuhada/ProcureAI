import datetime
import uuid
from sqlalchemy import Column, String, DateTime, JSON
from app.db.base import Base

class PurchaseRequisition(Base):
    __tablename__ = "purchase_requisitions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pr_number = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)
    department = Column(String, nullable=True)
    status = Column(String, default="DRAFT", nullable=False)  # DRAFT, SUBMITTED
    structured_requirement = Column(JSON, nullable=True)
    demand_analysis = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

import datetime
import uuid
from sqlalchemy import Column, String, Integer, DateTime
from app.db.base import Base

class PipelineOrder(Base):
    __tablename__ = "pipeline_orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_name = Column(String, index=True, nullable=False)
    order_type = Column(String, nullable=False)  # 'PR' or 'PO'
    reference_id = Column(String, unique=True, index=True, nullable=False)
    requester = Column(String, nullable=True)
    vendor = Column(String, nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    status = Column(String, default="PENDING_APPROVAL", nullable=False)
    expected_delivery = Column(String, nullable=True)
    department_id = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

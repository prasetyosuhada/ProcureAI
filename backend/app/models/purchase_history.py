import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime
from app.db.base import Base

class PurchaseHistory(Base):
    __tablename__ = "purchase_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_name = Column(String, index=True, nullable=False)
    department_id = Column(String, index=True, nullable=True)
    last_12_months_total = Column(Integer, default=0, nullable=False)
    average_order_quantity = Column(Integer, default=0, nullable=False)
    last_order_date = Column(String, nullable=True)
    average_unit_cost_usd = Column(Float, default=0.0, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

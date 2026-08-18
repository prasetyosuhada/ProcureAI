import datetime
import uuid
from sqlalchemy import Column, String, JSON, DateTime
from app.db.base import Base

class ProcurementPolicy(Base):
    __tablename__ = "procurement_policies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_key = Column(String, unique=True, index=True, nullable=False)
    item_category = Column(String, nullable=False)
    policy_text = Column(String, nullable=False)
    approval_rules = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

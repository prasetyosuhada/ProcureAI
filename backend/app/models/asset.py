import datetime
import uuid
from sqlalchemy import Column, String, Integer, DateTime
from app.db.base import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_name = Column(String, index=True, nullable=False)
    department_id = Column(String, index=True, nullable=True)
    currently_unused = Column(Integer, default=0, nullable=False)
    scheduled_returns_next_30_days = Column(Integer, default=0, nullable=False)
    total_available_soon = Column(Integer, default=0, nullable=False)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

import datetime
import uuid
from sqlalchemy import Column, String, JSON, DateTime
from app.db.base import Base

class ProcurementCategory(Base):
    __tablename__ = "procurement_categories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id = Column(String, unique=True, index=True, nullable=False)
    category_name = Column(String, nullable=False)
    keywords = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

import datetime
import uuid
from sqlalchemy import Column, String, JSON, DateTime
from app.db.base import Base

class StandardSpecification(Base):
    __tablename__ = "standard_specifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id = Column(String, index=True, nullable=False)
    item_name = Column(String, index=True, nullable=False)
    standard_models = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

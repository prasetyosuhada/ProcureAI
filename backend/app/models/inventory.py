import datetime
import uuid
from sqlalchemy import Column, String, Integer, DateTime
from app.db.base import Base

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_name = Column(String, index=True, nullable=False)
    category_id = Column(String, nullable=True)
    available_quantity = Column(Integer, default=0, nullable=False)
    location = Column(String, nullable=True)
    condition = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

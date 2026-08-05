from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class GRLineItemSchema(BaseModel):
    item_name: str = Field(..., description="Received item description")
    quantity_received: int = Field(..., ge=0, description="Quantity actually received")
    condition_notes: str | None = Field("Good", description="Condition or quality notes")

    model_config = ConfigDict(from_attributes=True)


class GRCreateSchema(BaseModel):
    po_id: UUID = Field(..., description="Target Purchase Order ID")
    delivery_note_ref: str = Field(..., min_length=2, description="Vendor delivery slip or tracking number")
    line_items: list[GRLineItemSchema] = Field(..., min_length=1, description="List of received items")

    model_config = ConfigDict(from_attributes=True)


class GRResponseSchema(BaseModel):
    id: UUID
    gr_number: str
    po_id: UUID
    received_by_id: UUID
    delivery_note_ref: str
    status: str
    line_items: list[GRLineItemSchema]
    received_at: datetime

    model_config = ConfigDict(from_attributes=True)

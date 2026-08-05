from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class POLineItemSchema(BaseModel):
    item_name: str = Field(..., description="Item description")
    category: str = Field(..., description="Item category")
    quantity: int = Field(..., gt=0, description="Ordered quantity")
    unit_price: Decimal = Field(..., gt=0, description="Agreed unit price")
    total: Decimal = Field(..., description="Line total amount")

    model_config = ConfigDict(from_attributes=True)


class POCreateSchema(BaseModel):
    vendor_id: UUID = Field(..., description="Target vendor ID")
    currency: str = Field("USD", min_length=3, max_length=3, description="Currency code")
    line_items: list[POLineItemSchema] | None = Field(None, description="Optional line items override")

    model_config = ConfigDict(from_attributes=True)


class POResponseSchema(BaseModel):
    id: UUID
    po_number: str
    pr_id: UUID
    vendor_id: UUID
    status: str
    total_amount: Decimal
    currency: str
    line_items: list[POLineItemSchema]
    issued_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

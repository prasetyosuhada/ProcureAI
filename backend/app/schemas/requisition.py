from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class PRItemSchema(BaseModel):
    item_name: str = Field(..., description="Name of the requested item")
    category: str = Field(..., description="Item category (e.g. Hardware, Software, Office)")
    quantity: int = Field(..., gt=0, description="Quantity requested")
    estimated_unit_price: Decimal = Field(..., gt=0, description="Estimated unit price")

    model_config = ConfigDict(from_attributes=True)


class PRCreateSchema(BaseModel):
    budget_id: UUID = Field(..., description="Target budget ID")
    justification: str = Field(..., min_length=5, description="Business justification for the PR")
    line_items: list[PRItemSchema] = Field(..., min_length=1, description="List of items requested")

    model_config = ConfigDict(from_attributes=True)


class PRResponseSchema(BaseModel):
    id: UUID
    pr_number: str
    requester_id: UUID
    budget_id: UUID
    status: str
    justification: str
    total_amount: Decimal
    line_items: list[PRItemSchema]
    validation_result: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

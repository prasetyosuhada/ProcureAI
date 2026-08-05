from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class InvoiceLineItemSchema(BaseModel):
    description: str = Field(..., description="Billed item description")
    quantity: int = Field(..., gt=0, description="Billed quantity")
    unit_price: Decimal = Field(..., gt=0, description="Billed unit price")
    total: Decimal = Field(..., description="Billed line total amount")

    model_config = ConfigDict(from_attributes=True)


class InvoiceCreateSchema(BaseModel):
    invoice_number: str = Field(..., min_length=1, description="Vendor invoice number")
    po_id: UUID = Field(..., description="Referenced Purchase Order ID")
    vendor_id: UUID = Field(..., description="Issuing Vendor ID")
    invoice_date: date = Field(..., description="Date on physical invoice")
    total_amount: Decimal = Field(..., gt=0, description="Grand total amount")
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Tax amount")
    line_items: list[InvoiceLineItemSchema] = Field(..., min_length=1, description="Billed line items")

    model_config = ConfigDict(from_attributes=True)


class InvoiceResponseSchema(BaseModel):
    id: UUID
    invoice_number: str
    po_id: UUID
    vendor_id: UUID
    submitted_by_id: UUID
    invoice_date: date
    total_amount: Decimal
    tax_amount: Decimal
    line_items: list[InvoiceLineItemSchema]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

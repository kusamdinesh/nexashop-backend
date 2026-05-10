from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int

class OrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: int
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    customer_id: UUID
    items: list[OrderItemCreate]
    notes: Optional[str] = None

class OrderStatusUpdate(BaseModel):
    status: str

class OrderResponse(BaseModel):
    id: UUID
    order_number: str
    customer_id: UUID
    status: str
    subtotal: float
    tax: float
    total: float
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: list[OrderItemResponse] = []

    class Config:
        from_attributes = True

class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
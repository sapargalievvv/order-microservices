from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.db.models import OrderStatus
from decimal import Decimal


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class OrderItem(OrderItemCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    name: str
    price: Decimal = Field(max_digits=10, decimal_places=2)


class OrderCreate(BaseModel):
    order_items: list[OrderItemCreate]


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # id: int
    user_id: str
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    status: OrderStatus
    created_at: datetime
    items: list[OrderItem]

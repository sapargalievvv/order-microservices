from datetime import datetime
from pydantic import BaseModel
from app.db.models import OrderStatus


class OrderCreate(BaseModel):
    # user_id: int
    title: str
    amount: float


class OrderResponse(BaseModel):
    id: int
    user_id: int
    title: str
    amount: float
    status: OrderStatus
    # created_at: datetime

    class Config:
        from_attributes = True

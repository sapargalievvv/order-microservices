import enum

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.sql import func

from app.db.session import Base  # твой Base
from datetime import datetime, timezone


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=False)

    # ВАЖНО: передаем OrderStatus и указываем native_enum=True (или name="orderstatus")
    status = Column(
        SQLEnum(OrderStatus, name="orderstatus", create_type=False),
        default=OrderStatus.PENDING,
        nullable=False,
    )

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

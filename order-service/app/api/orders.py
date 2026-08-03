import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.db.models import Order, OrderStatus
from app.db.session import get_db
from app.schemas.order import OrderCreate, OrderResponse
from app.services.kafka_producer import send_order_created_event
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/orders", tags=["Orders"])


# Вспомогательная функция для генерации ключа кеша
def get_order_cache_key(order_id: int) -> str:
    return f"order:{order_id}"


@router.get("/", response_model=list[OrderResponse])
async def get_alL_orders(db: AsyncSession = Depends(get_db)):
    query = select(Order)
    res = await db.execute(query)
    orders = res.scalars().all()
    return orders


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    new_order = Order(
        user_id=user_id,
        title=order_in.title,
        amount=order_in.amount,
        # status=OrderStatus.PENDING,  # <-- Используем Enum значение
    )
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    # Отправляем событие в Kafka для других сервисов
    event_payload = {
        "event": "order_created",
        "order_id": new_order.id,
        "user_id": new_order.user_id,
        "title": new_order.title,
        "amount": new_order.amount,
        "status": new_order.status.value,
    }
    await send_order_created_event(event_payload)

    return new_order


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)
):
    cache_key = get_order_cache_key(order_id)

    # 1. Сначала пробуем получить данные из Redis (Cache Hit)
    cached_data = await redis.get(cache_key)
    if cached_data:
        print(f"--- REDIS CACHE HIT for order {order_id} ---")
        return json.loads(cached_data)

    # 2. Если в Redis ничего нет — идем в PostgreSQL (Cache Miss)
    print(f"--- REDIS CACHE MISS for order {order_id}. Querying Postgres... ---")
    query = select(Order).where(Order.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Преобразуем объект SQLAlchemy в Pydantic для удобной JSON-сериализации
    order_response = OrderResponse.model_validate(order)

    # 3. Сохраняем в Redis с временем жизни (TTL) 300 секунд
    await redis.set(cache_key, order_response.model_dump_json(), ex=300)

    return order_response

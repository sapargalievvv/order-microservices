import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_user_id
from app.core.redis import get_redis
from app.db.models import Order, OrderItem
from app.db.session import get_db
from app.schemas.order import OrderCreate, OrderResponse
from app.clients.products import (
    ProductNotFound,
    ProductsClient,
    ProductsUnavailable,
    get_products_client,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


# Вспомогательная функция для генерации ключа кеша
def get_order_cache_key(order_id: int) -> str:
    return f"order:{order_id}"


@router.get("/", response_model=list[OrderResponse])
async def get_alL_orders(db: AsyncSession = Depends(get_db)):
    query = select(Order).options(selectinload(Order.items))
    res = await db.execute(query)
    orders = res.scalars().all()
    return orders


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=OrderResponse)
async def create_order(
    order_in: OrderCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    products_client: ProductsClient = Depends(get_products_client),
):
    # Запрашиваем товары параллельно, а не по одному в цикле
    try:
        products = await asyncio.gather(
            *(
                products_client.get_product(item.product_id)
                for item in order_in.order_items
            )
        )
    except ProductNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {exc.product_id} not found",
        )
    except ProductsUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Products service unavailable",
        )

    # Цену фиксируем в момент заказа: изменение прайса завтра не должно менять заказ
    items = [
        OrderItem(
            product_id=product.id,
            name=product.name,
            price=product.price,
            quantity=item.quantity,
        )
        for product, item in zip(products, order_in.order_items)
    ]

    # items передаём в конструктор: у pending-объекта нет старой коллекции,
    # которую SQLAlchemy пришлось бы подгружать лениво ради delete-orphan
    order = Order(
        user_id=user_id,
        amount=sum(item.price * item.quantity for item in items),
        items=items,
    )

    db.add(order)
    await db.commit()

    return order


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
    query = select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    result = await db.execute(query)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Преобразуем объект SQLAlchemy в Pydantic для удобной JSON-сериализации
    order_response = OrderResponse.model_validate(order)

    # 3. Сохраняем в Redis с временем жизни (TTL) 300 секунд
    await redis.set(cache_key, order_response.model_dump_json(), ex=300)

    return order_response

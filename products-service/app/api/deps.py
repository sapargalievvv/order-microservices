from app.db.session import get_db
from app.services.product_service import ProductService
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.redis import get_redis
from redis.asyncio import Redis


async def get_product_service(
    db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)
) -> ProductService:
    return ProductService(db, redis)

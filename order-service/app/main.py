from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.orders import router as orders_router

from app.core.redis import close_redis, init_redis

from app.services.kafka_producer import init_kafka, stop_kafka
from app.db.session import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Старт ресурсов
    await init_redis()
    await init_kafka()
    yield
    # Завершение ресурсов
    await close_redis()
    await stop_kafka()


app = FastAPI(title="Order Service", lifespan=lifespan)
app.include_router(orders_router)

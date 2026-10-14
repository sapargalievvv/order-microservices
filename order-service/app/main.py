from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.orders import router as orders_router
from app.clients.products import close_products_client, init_products_client
from app.core.redis import close_redis, init_redis
from app.db.session import Base, engine
from app.services.kafka_producer import init_kafka, stop_kafka


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Старт ресурсов
    await init_redis()
    await init_kafka()
    await init_products_client()
    yield
    # Завершение ресурсов
    await close_redis()
    await stop_kafka()
    await close_products_client()


app = FastAPI(title="Order Service", lifespan=lifespan)
app.include_router(orders_router)

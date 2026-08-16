from contextlib import asynccontextmanager

from app.api.products import router as products_router
from app.core.config import settings
from app.core.redis import close_redis, init_redis
from app.services.kafka_producer import init_kafka, stop_kafka
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    await init_kafka()
    yield
    await close_redis()
    await stop_kafka()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
app.include_router(products_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "products_service"}

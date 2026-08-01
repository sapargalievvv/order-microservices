from contextlib import asynccontextmanager

from app.api.products import router as products_router
from app.core.config import settings
from app.core.redis import close_redis, init_redis
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    yield
    await close_redis()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
app.include_router(products_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "products_service"}

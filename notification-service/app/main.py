import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.services.kafka_consumer import consume_notifications

consumer_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_task
    # Запускаем консьюмер в фоновой asyncio-задаче
    consumer_task = asyncio.create_task(consume_notifications())
    yield
    # Отменяем задачу при остановке сервиса
    if consumer_task:
        consumer_task.cancel()


app = FastAPI(title="Notification Service", lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "ok"}

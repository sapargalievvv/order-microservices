import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.services.kafka_consumer import (
    consume_notifications,
    consume_product_stock_notifications,
)

consumer_tasks: list[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Каждый консьюмер живёт в своей фоновой asyncio-задаче
    consumer_tasks.append(asyncio.create_task(consume_notifications()))
    consumer_tasks.append(asyncio.create_task(consume_product_stock_notifications()))
    yield
    # cancel() только просит задачу остановиться. Без ожидания процесс успеет
    # умереть раньше, чем консьюмеры закоммитят оффсеты в своих finally.
    for task in consumer_tasks:
        task.cancel()
    # return_exceptions=True — иначе CancelledError вылетит из gather наружу
    await asyncio.gather(*consumer_tasks, return_exceptions=True)
    consumer_tasks.clear()


app = FastAPI(title="Notification Service", lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "ok"}

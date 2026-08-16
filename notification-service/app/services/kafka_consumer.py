import asyncio
import json

from aiokafka import AIOKafkaConsumer
from app.core.config import settings


async def consume_notifications():
    consumer = AIOKafkaConsumer(
        "orders.v1.created",  # Имя топика
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="notification_group",  # Идентификатор группы консьюмеров
        auto_offset_reset="earliest",  # Читать с самого начала, если нет сохраненного оффсета
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )

    await consumer.start()
    print("--- KAFKA CONSUMER STARTED: Waiting for messages... ---")

    try:
        async for msg in consumer:
            event_data = msg.value
            print(f"--- KAFKA CONSUMED EVENT: {msg.topic} ---")

            # Бизнес-логика отправки уведомления
            await process_notification(event_data)

    finally:
        await consumer.stop()


async def process_notification(event_data: dict):
    user_id = event_data.get("user_id")
    order_id = event_data.get("order_id")
    amount = event_data.get("amount")

    # Имитация отправки Email / Push
    print(
        f"✉️ [NOTIFICATION SENT] User #{user_id}: "
        f"Ваш заказ #{order_id} на сумму ${amount} успешно создан!"
    )


STOCK_CHANGED = "products.v1.stock_changed"


async def consume_product_stock_notifications():
    consumer = AIOKafkaConsumer(
        STOCK_CHANGED,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="stock_notification_group",  # Своя группа: свои оффсеты, независимое масштабирование
        auto_offset_reset="earliest",  # Читать с самого начала, если нет сохраненного оффсета
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8"),
    )
    await consumer.start()
    try:
        async for msg in consumer:
            event_data = msg.value
            print("event data", msg.key, event_data)

    finally:
        await consumer.stop()

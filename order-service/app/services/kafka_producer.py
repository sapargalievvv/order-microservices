import json

from aiokafka import AIOKafkaProducer
from app.core.config import settings

kafka_producer: AIOKafkaProducer | None = None


async def init_kafka() -> None:
    global kafka_producer
    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        # Сериализуем dict в JSON, а затем в байты
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await kafka_producer.start()


async def stop_kafka() -> None:
    global kafka_producer
    if kafka_producer:
        await kafka_producer.stop()


async def send_order_created_event(order_data: dict) -> None:
    if kafka_producer:
        await kafka_producer.send_and_wait(topic="orders.v1.created", value=order_data)
        print(f"--- KAFKA PRODUCED EVENT: orders.v1.created -> {order_data} ---")

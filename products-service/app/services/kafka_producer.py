from aiokafka import AIOKafkaProducer
from app.core.config import settings
import json
from app.core.events import STOCK_CHANGED

kafka_producer: AIOKafkaProducer | None = None


async def init_kafka() -> None:
    global kafka_producer

    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8"),
    )

    await kafka_producer.start()


async def stop_kafka() -> None:
    if kafka_producer:
        await kafka_producer.stop()


async def send_stock_changed_event(
    product_id: int, name: str, old_stock: int, new_stock: int
) -> None:
    event = {
        "product_id": product_id,
        "name": name,
        "old_stock": old_stock,
        "new_stock": new_stock,
    }
    if kafka_producer:
        await kafka_producer.send_and_wait(
            STOCK_CHANGED, key=str(product_id), value=event
        )

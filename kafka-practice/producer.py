from aiokafka import AIOKafkaProducer
import random
import asyncio
import json


async def main():
    producer = AIOKafkaProducer(
        bootstrap_servers="localhost:9094",
        key_serializer=lambda k: k.encode("utf-8"),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await producer.start()

    try:
        for i in range(10):
            user_id = random.choice(["u1", "u2", "u3"])
            event = {"user_id": user_id, "page": f"/product/{i}"}
            await producer.send_and_wait(
                topic="clicks.v1.happened", value=event, key=user_id
            )
            await asyncio.sleep(0.5)
    finally:
        await producer.stop()


asyncio.run(main())

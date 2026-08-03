import asyncio
from collections import Counter
import json
from aiokafka import AIOKafkaConsumer

counter = Counter()


async def main():
    consumer = AIOKafkaConsumer(
        "clicks.v1.happened",
        bootstrap_servers="localhost:9094",
        group_id="clicks_counter",
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8"),
        enable_auto_commit=False,
    )

    await consumer.start()

    try:
        async for msg in consumer:
            counter[msg.key] += 1
            await asyncio.sleep(2)
            print(
                f"p{msg.partition} off={msg.offset} {msg.key} -> {msg.value} | {dict(counter)}"
            )
            await consumer.commit()
    finally:
        await consumer.stop()


asyncio.run(main())

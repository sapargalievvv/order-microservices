"""Наполняет products_db тестовыми товарами.

Запуск из корня сервиса:
    ./.venv/bin/python -m scripts.seed
"""

import asyncio
import random
from decimal import Decimal

from sqlalchemy import func, select

from app.db.models import Product
from app.db.session import AsyncSessionLocal, engine

# Из этих кусков собираем 50 осмысленных названий

CATEGORIES = {
    "Мышь": (990, 7900),
    "Клавиатура": (1990, 15900),
    "Монитор": (14900, 89900),
    "Наушники": (2490, 34900),
    "Ноутбук": (49900, 249900),
    "Веб-камера": (2990, 18900),
    "Микрофон": (3490, 29900),
    "SSD": (3990, 24900),
    "Роутер": (2990, 19900),
    "Powerbank": (1490, 9900),
}
BRANDS = ["Logitech", "Keychron", "Samsung", "Xiaomi", "HyperX", "ASUS", "Sony", "Acer"]
SUFFIXES = ["Pro", "Lite", "Max", "Air", "Ultra"]

TOTAL = 50


def build_products() -> list[Product]:
    random.seed(42)  # фиксируем сид, чтобы прогоны были воспроизводимы
    products: list[Product] = []

    for i in range(TOTAL):
        category, (min_price, max_price) = list(CATEGORIES.items())[i % len(CATEGORIES)]
        brand = BRANDS[i % len(BRANDS)]
        suffix = SUFFIXES[i % len(SUFFIXES)]
        name = f"{brand} {category} {suffix} {i + 1}"

        price = Decimal(random.randrange(min_price, max_price, 10)).quantize(
            Decimal("0.01")
        )

        products.append(
            Product(
                name=name,
                description=f"{category} {brand} для дома и офиса",
                price=price,
                stock=random.randint(0, 120),
                image_url=f"https://picsum.photos/seed/product{i + 1}/600/600",
            )
        )

    return products


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(Product))
        if count:
            print(f"В таблице уже {count} товаров — сид пропущен.")
            print("Чтобы пересоздать: DELETE FROM products; и запустить снова.")
            return

        session.add_all(build_products())
        await session.commit()
        print(f"Добавлено товаров: {TOTAL}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())

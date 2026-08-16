from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Product
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.schemas.reserve import (
    ReservedItem,
    ReserveItem,
    ReserveResponse,
)
from app.services.exceptions import InsufficientStock, ProductNotFound
from redis.asyncio import Redis


class ProductService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis

    async def get_all(self) -> Sequence[Product]:
        res = await self.db.execute(select(Product))
        return res.scalars().all()

    async def get_by_id(self, product_id):
        res = await self.db.execute(select(Product).where(Product.id == product_id))
        return res.scalar_one_or_none()

    async def create(self, product_create: ProductCreate) -> Product:
        product = Product(**product_create.model_dump())
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def update(self, product: Product, data: ProductUpdate) -> Product:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        await self.db.flush()
        await self.db.refresh(product)
        await self.invalidate(product.id)
        return product

    async def delete(self, product: Product) -> None:
        product_id = product.id
        await self.db.delete(product)
        await self.db.flush()
        await self.invalidate(product_id)

    async def process_order_items(
        self, products_in: list[ReserveItem]
    ) -> ReserveResponse:
        ids = sorted({i.product_id for i in products_in})

        # FOR UPDATE держит строки до конца транзакции, ORDER BY id задаёт
        # одинаковый порядок блокировок во всех запросах — иначе дедлок
        res = await self.db.execute(
            select(Product)
            .where(Product.id.in_(ids))
            .order_by(Product.id)
            .with_for_update()
        )
        products = {p.id: p for p in res.scalars().all()}

        missing = set(ids) - products.keys()
        if missing:
            raise ProductNotFound(missing)

        # Сначала проверяем все позиции и ничего не списываем: резерв
        # проходит либо целиком, либо никак
        for item in products_in:
            product = products[item.product_id]
            if product.stock < item.quantity:
                raise InsufficientStock(item.product_id, item.quantity, product.stock)

        # Дошли сюда — значит хватает на всё
        reserved = []
        for item in products_in:
            product = products[item.product_id]
            product.stock -= item.quantity
            reserved.append(
                ReservedItem(
                    product_id=product.id,
                    quantity=item.quantity,
                    name=product.name,
                    price=product.price,
                )
            )

        await self.db.flush()

        for pid in ids:
            await self.invalidate(pid)

        total = sum(i.price * i.quantity for i in reserved)
        return ReserveResponse(items=reserved, total=total)

    def _key(self, product_id: int) -> str:
        return f"product:{product_id}"

    CACHE_TTL = 300

    async def get_cached(self, product_id: int) -> ProductResponse | None:
        cached = await self.redis.get(self._key(product_id))

        if cached:
            return ProductResponse.model_validate_json(cached)

        product = await self.get_by_id(product_id)
        if not product:
            return None

        response = ProductResponse.model_validate(product)
        await self.redis.set(
            self._key(product_id), response.model_dump_json(), ex=self.CACHE_TTL
        )

        return response

    async def invalidate(self, product_id: int) -> None:
        await self.redis.delete(self._key(product_id))

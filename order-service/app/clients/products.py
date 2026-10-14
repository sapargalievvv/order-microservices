from decimal import Decimal

import httpx
from pydantic import BaseModel

from app.core.config import settings

# Один клиент на всё приложение: пул соединений переиспользуется между запросами.
# None вне жизненного цикла приложения — как redis_client и kafka_producer.
http_client: httpx.AsyncClient | None = None


async def init_products_client() -> None:
    global http_client
    http_client = httpx.AsyncClient(
        base_url=settings.PRODUCTS_SERVICE_URL,
        # Без явных таймаутов один зависший ответ соседа занимает наш воркер надолго
        timeout=httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=1.0),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )


async def close_products_client() -> None:
    global http_client
    if http_client:
        await http_client.aclose()


class ProductNotFound(Exception):
    def __init__(self, product_id: int) -> None:
        self.product_id = product_id
        super().__init__(f"Product not found: {product_id}")


class ProductsUnavailable(Exception):
    pass


class ProductDTO(BaseModel):
    """Контракт products-service — только те поля, что нужны заказу."""

    id: int
    name: str
    price: Decimal


class ProductsClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def get_product(self, product_id: int) -> ProductDTO:
        try:
            response = await self.client.get(f"/products/{product_id}")
        except httpx.RequestError as exc:
            # Сеть/таймаут — наружу отдаём доменную ошибку, httpx не протекает в роутер
            raise ProductsUnavailable(str(exc)) from exc

        if response.status_code == 404:
            raise ProductNotFound(product_id)
        if response.is_error:
            raise ProductsUnavailable(
                f"products-service ответил {response.status_code}"
            )

        return ProductDTO.model_validate(response.json())


async def get_products_client() -> ProductsClient:
    return ProductsClient(http_client)

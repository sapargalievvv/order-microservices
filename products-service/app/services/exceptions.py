"""Доменные ошибки сервисного слоя.

Про HTTP тут ничего не знают — статусы проставляет роутер.
"""


class ProductNotFound(Exception):
    def __init__(self, product_ids: set[int]):
        self.product_ids = product_ids
        super().__init__(f"Products not found: {sorted(product_ids)}")


class InsufficientStock(Exception):
    def __init__(self, product_id: int, requested: int, available: int):
        self.product_id = product_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Product {product_id}: requested {requested}, available {available}"
        )

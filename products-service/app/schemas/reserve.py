from pydantic import BaseModel, Field, field_validator
from decimal import Decimal


class ReserveItem(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class ReserveRequest(BaseModel):
    items: list[ReserveItem] = Field(min_length=1)

    @field_validator("items")
    @classmethod
    def no_duplicate_products(cls, items: list[ReserveItem]) -> list[ReserveItem]:
        # Один товар двумя строками сломал бы арифметику резерва
        ids = [i.product_id for i in items]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate product_id in items")
        return items


class ReservedItem(ReserveItem):
    name: str
    price: Decimal


class ReserveResponse(BaseModel):
    items: list[ReservedItem]
    total: Decimal

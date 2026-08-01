from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_product_service
from app.db.models import Product
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


# Общий хелпер: достаём товар или отдаём 404.
# HTTP-ошибки живут в роутере, сервис про них ничего не знает.
async def get_product_or_404(product_id: int, service: ProductService) -> Product:
    product = await service.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/", response_model=list[ProductResponse])
async def list_products(service: ProductService = Depends(get_product_service)):
    return await service.get_all()


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    service: ProductService = Depends(get_product_service),
):
    return await service.create(product_in)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
):
    product = await service.get_cached(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_in: ProductUpdate,
    service: ProductService = Depends(get_product_service),
):
    product = await get_product_or_404(product_id, service)
    return await service.update(product, product_in)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
):
    product = await get_product_or_404(product_id, service)
    await service.delete(product)

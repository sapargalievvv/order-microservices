from app.api.deps import get_product_service
from app.core.auth import get_current_user_id
from app.db.models import Product
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import ProductService
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.kafka_producer import send_stock_changed_event
from app.schemas.reserve import ReserveRequest, ReserveResponse
from app.services.exceptions import InsufficientStock, ProductNotFound

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
    user_id: str = Depends(get_current_user_id),
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
    # user_id: str = Depends(get_current_user_id),
):
    product = await get_product_or_404(product_id, service)
    fields = product_in.model_dump(exclude_unset=True)
    old_stock = product.stock
    product = await service.update(product, product_in)

    if "stock" in fields and old_stock != product.stock:
        await send_stock_changed_event(
            product_id, product.name, old_stock, product.stock
        )
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
    user_id: str = Depends(get_current_user_id),
):
    product = await get_product_or_404(product_id, service)
    await service.delete(product)


@router.post("/internal/reserve", response_model=ReserveResponse)
async def reserve_products(
    reserve_request: ReserveRequest,
    service: ProductService = Depends(get_product_service),
    user_id: str = Depends(get_current_user_id),
):
    try:
        return await service.process_order_items(reserve_request.items)
    except ProductNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "products_not_found", "product_ids": sorted(exc.product_ids)},
        )
    except InsufficientStock as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "insufficient_stock",
                "product_id": exc.product_id,
                "requested": exc.requested,
                "available": exc.available,
            },
        )

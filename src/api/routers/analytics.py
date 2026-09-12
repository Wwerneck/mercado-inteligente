from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_repository
from src.api.repository import AnalyticsRepository
from src.api.schemas import (
    CategoryMetric,
    MarketplaceOverview,
    PaginatedResponse,
    SellerItem,
    SellerItemMetric,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=list[MarketplaceOverview])
def get_overview(
    repository: Annotated[AnalyticsRepository, Depends(get_repository)],
) -> list[dict]:
    return repository.marketplace_overview()


@router.get("/categories", response_model=PaginatedResponse)
def get_category_metrics(
    repository: Annotated[AnalyticsRepository, Depends(get_repository)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    items, total = repository.category_metrics(limit=limit, offset=offset)
    return {"items": items, "limit": limit, "offset": offset, "total": total}


@router.get("/categories/{category_id}", response_model=CategoryMetric)
def get_category_metric(
    category_id: str,
    repository: Annotated[AnalyticsRepository, Depends(get_repository)],
) -> dict:
    record = repository.category_metric(category_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return record


@router.get("/seller-items", response_model=PaginatedResponse)
def get_seller_item_metrics(
    repository: Annotated[AnalyticsRepository, Depends(get_repository)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    items, total = repository.seller_item_metrics(limit=limit, offset=offset)
    validated_items = [SellerItemMetric(**item).model_dump() for item in items]
    return {"items": validated_items, "limit": limit, "offset": offset, "total": total}


@router.get("/items", response_model=PaginatedResponse)
def get_seller_items(
    repository: Annotated[AnalyticsRepository, Depends(get_repository)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    seller_id: str | None = None,
    category_id: str | None = None,
    status: str | None = None,
) -> dict:
    items, total = repository.seller_items(
        limit=limit,
        offset=offset,
        seller_id=seller_id,
        category_id=category_id,
        status=status,
    )
    validated_items = [SellerItem(**item).model_dump() for item in items]
    return {"items": validated_items, "limit": limit, "offset": offset, "total": total}


@router.get("/price-history", response_model=PaginatedResponse)
def get_price_history(
    repository: Annotated[AnalyticsRepository, Depends(get_repository)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    items, total = repository.price_history(limit=limit, offset=offset)
    return {"items": items, "limit": limit, "offset": offset, "total": total}

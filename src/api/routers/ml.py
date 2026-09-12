from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_repository
from src.api.repository import AnalyticsRepository
from src.api.schemas import MLCategoryScore, PaginatedResponse

router = APIRouter(prefix="/ml", tags=["machine-learning"])


@router.get("/opportunity-score", response_model=PaginatedResponse)
def get_opportunity_scores(
    repository: Annotated[AnalyticsRepository, Depends(get_repository)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    items, total = repository.ml_scores(limit=limit, offset=offset)
    return {"items": items, "limit": limit, "offset": offset, "total": total}


@router.get("/anomalies", response_model=list[MLCategoryScore])
def get_anomalies(
    repository: Annotated[AnalyticsRepository, Depends(get_repository)],
) -> list[dict]:
    return repository.anomalies()


@router.get("/metadata")
def get_ml_metadata(
    repository: Annotated[AnalyticsRepository, Depends(get_repository)],
) -> dict:
    return repository.ml_metadata()


@router.get("/advanced-metadata")
def get_advanced_ml_metadata(
    repository: Annotated[AnalyticsRepository, Depends(get_repository)],
) -> dict:
    return repository.advanced_ml_metadata()


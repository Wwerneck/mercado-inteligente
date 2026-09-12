from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_repository
from src.api.repository import AnalyticsRepository
from src.api.schemas import PaginatedResponse, PipelineRunSummary

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/runs", response_model=PaginatedResponse)
def get_pipeline_runs(
    repository: Annotated[AnalyticsRepository, Depends(get_repository)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, Any]:
    items, total = repository.pipeline_runs(limit=limit, offset=offset)
    validated_items = [PipelineRunSummary(**item).model_dump() for item in items]
    return {"items": validated_items, "limit": limit, "offset": offset, "total": total}


@router.get("/runs/latest")
def get_latest_pipeline_run(
    repository: Annotated[AnalyticsRepository, Depends(get_repository)],
) -> dict[str, Any]:
    record = repository.latest_pipeline_run()
    if record is None:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return record


@router.get("/observability")
def get_pipeline_observability(
    repository: Annotated[AnalyticsRepository, Depends(get_repository)],
) -> dict[str, Any]:
    record = repository.pipeline_observability()
    if not record:
        raise HTTPException(status_code=404, detail="Pipeline observability not found")
    return record


@router.get("/runs/{run_id}")
def get_pipeline_run(
    run_id: str,
    repository: Annotated[AnalyticsRepository, Depends(get_repository)],
) -> dict[str, Any]:
    record = repository.pipeline_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return record

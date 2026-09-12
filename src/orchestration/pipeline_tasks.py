import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.analytics.gold import build_gold
from src.config.settings import get_settings
from src.database.dimensional import build_dimensional_model
from src.database.duckdb_repository import load_dimensional_model
from src.ingestion.run_authenticated_collection import run_authenticated_collection
from src.ingestion.run_batch_collection import run_batch_collection
from src.ml.run_phase_6 import run_ml_pipeline
from src.ml.run_phase_7 import run_advanced_ml_pipeline
from src.processing.silver import build_silver
from src.storage.lake import read_parquet_dataset
from src.validation.data_quality import (
    QualityCheckResult,
    raise_on_failed_checks,
    require_columns,
    require_non_null,
)

logger = logging.getLogger(__name__)


def _manifest_path(data_dir: Path, run_id: str) -> Path:
    safe_run_id = run_id.replace(":", "-").replace("/", "-")
    return data_dir / "pipeline_runs" / f"{safe_run_id}.json"


def write_manifest(data_dir: Path, run_id: str, payload: dict[str, Any]) -> Path:
    path = _manifest_path(data_dir, run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def build_observability_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    tasks = manifest.get("tasks", {})
    row_counts: dict[str, int] = {}
    task_statuses: dict[str, str] = {}
    if isinstance(tasks, dict):
        for task_name, task_payload in tasks.items():
            task_statuses[task_name] = _task_status(task_payload)
            for output in _iter_task_outputs(task_payload):
                entity = output.get("entity")
                rows = output.get("rows")
                if isinstance(entity, str) and isinstance(rows, int):
                    row_counts[entity] = row_counts.get(entity, 0) + rows

    return {
        "run_id": manifest.get("run_id"),
        "status": manifest.get("status"),
        "started_at": manifest.get("started_at"),
        "finished_at": manifest.get("finished_at"),
        "duration_seconds": manifest.get("duration_seconds"),
        "task_count": len(tasks) if isinstance(tasks, dict) else 0,
        "task_statuses": task_statuses,
        "row_counts": row_counts,
        "total_rows_processed": sum(row_counts.values()),
    }


def write_observability_summary(data_dir: Path, manifest: dict[str, Any]) -> Path:
    path = data_dir / "gold" / "pipeline_observability.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(build_observability_summary(manifest), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return path


def _task_status(task_payload: Any) -> str:
    if isinstance(task_payload, dict) and isinstance(task_payload.get("status"), str):
        return task_payload["status"]
    return "success"


def _iter_task_outputs(task_payload: Any) -> list[dict[str, Any]]:
    if isinstance(task_payload, list):
        return [item for item in task_payload if isinstance(item, dict)]
    if isinstance(task_payload, dict):
        outputs = task_payload.get("outputs")
        if isinstance(outputs, list):
            return [item for item in outputs if isinstance(item, dict)]
    return []


def extract_marketplace_data(queries: list[str] | None = None) -> list[dict[str, object]]:
    settings = get_settings()
    selected_queries = queries or settings.public_queries
    outputs = run_batch_collection(selected_queries)
    logger.info(
        "Marketplace data extracted",
        extra={
            "pipeline": "airflow_marketplace_pipeline",
            "task": "extract_marketplace_data",
            "rows_processed": sum(int(output["rows"]) for output in outputs),
            "status": "success",
        },
    )
    return outputs


def extract_authenticated_marketplace_data() -> dict[str, Any]:
    settings = get_settings()
    if not settings.meli_enable_authenticated_collection:
        logger.info(
            "Authenticated marketplace extraction disabled",
            extra={
                "pipeline": "airflow_marketplace_pipeline",
                "task": "extract_authenticated_marketplace_data",
                "status": "skipped",
            },
        )
        return {
            "status": "skipped",
            "reason": "MELI_ENABLE_AUTHENTICATED_COLLECTION is false",
            "outputs": [],
        }

    if not settings.meli_token_store_path.exists():
        logger.info(
            "Authenticated marketplace extraction skipped",
            extra={
                "pipeline": "airflow_marketplace_pipeline",
                "task": "extract_authenticated_marketplace_data",
                "status": "skipped",
            },
        )
        return {
            "status": "skipped",
            "reason": f"OAuth token not found at {settings.meli_token_store_path}",
            "outputs": [],
        }

    outputs = run_authenticated_collection()
    logger.info(
        "Authenticated marketplace data extracted",
        extra={
            "pipeline": "airflow_marketplace_pipeline",
            "task": "extract_authenticated_marketplace_data",
            "rows_processed": sum(int(output["rows"]) for output in outputs),
            "status": "success",
        },
    )
    return {"status": "success", "outputs": outputs}


def validate_raw_data() -> list[dict[str, Any]]:
    settings = get_settings()
    checks: list[QualityCheckResult] = []
    for entity in ["domain_discovery", "categories"]:
        frame = read_parquet_dataset(settings.data_dir / "bronze" / entity)
        checks.extend(
            [
                require_columns(frame, ["ingested_at", "source", "endpoint", "record_id", "payload"], f"bronze_{entity}"),
                require_non_null(frame, ["ingested_at", "source", "endpoint", "payload"], f"bronze_{entity}"),
            ]
        )
    raise_on_failed_checks(checks)
    return [check.__dict__ for check in checks]


def transform_silver() -> dict[str, str]:
    settings = get_settings()
    return build_silver(settings.data_dir)


def data_quality_checks() -> list[dict[str, Any]]:
    settings = get_settings()
    checks: list[QualityCheckResult] = []
    silver_requirements = {
        "categories.parquet": ["category_id", "category_name", "ingested_at"],
        "domain_discovery.parquet": ["domain_id", "category_id", "ingested_at"],
        "item_details.parquet": ["item_id", "ingested_at"],
    }
    for file_name, required_columns in silver_requirements.items():
        frame = pd.read_parquet(settings.data_dir / "silver" / file_name)
        dataset = file_name.replace(".parquet", "")
        checks.append(require_columns(frame, required_columns, dataset))
        checks.append(require_non_null(frame, required_columns, dataset))
    raise_on_failed_checks(checks)
    return [check.__dict__ for check in checks]


def build_gold_layer() -> dict[str, str]:
    settings = get_settings()
    return build_gold(settings.data_dir)


def publish_to_warehouse() -> dict[str, int]:
    settings = get_settings()
    model = build_dimensional_model(settings.data_dir)
    return load_dimensional_model(settings.duckdb_path, model)


def generate_ml_results() -> dict[str, str]:
    return run_ml_pipeline()


def generate_advanced_ml_results() -> dict[str, str]:
    return run_advanced_ml_pipeline()


def run_full_pipeline(query: str | None = None, run_id: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    selected_queries = [query] if query else settings.public_queries
    current_run_id = run_id or datetime.now(UTC).isoformat()
    started_at = datetime.now(UTC)
    manifest: dict[str, Any] = {
        "run_id": current_run_id,
        "started_at": started_at.isoformat(),
        "query": query,
        "queries": selected_queries,
        "status": "running",
        "tasks": {},
    }

    try:
        manifest["tasks"]["extract_marketplace_data"] = extract_marketplace_data(selected_queries)
        manifest["tasks"][
            "extract_authenticated_marketplace_data"
        ] = extract_authenticated_marketplace_data()
        manifest["tasks"]["validate_raw_data"] = validate_raw_data()
        manifest["tasks"]["transform_silver"] = transform_silver()
        manifest["tasks"]["data_quality_checks"] = data_quality_checks()
        manifest["tasks"]["build_gold"] = build_gold_layer()
        manifest["tasks"]["publish_to_warehouse"] = publish_to_warehouse()
        manifest["tasks"]["generate_ml_results"] = generate_ml_results()
        manifest["tasks"]["generate_advanced_ml_results"] = generate_advanced_ml_results()
        manifest["status"] = "success"
        return manifest
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["error"] = str(exc)
        raise
    finally:
        manifest["finished_at"] = datetime.now(UTC).isoformat()
        manifest["duration_seconds"] = (datetime.now(UTC) - started_at).total_seconds()
        manifest_path = write_manifest(settings.data_dir, current_run_id, manifest)
        observability_path = write_observability_summary(settings.data_dir, manifest)
        logger.info(
            "Pipeline manifest written",
            extra={
                "pipeline": "airflow_marketplace_pipeline",
                "task": "write_manifest",
                "status": manifest["status"],
            },
        )
        manifest["manifest_path"] = str(manifest_path)
        manifest["observability_path"] = str(observability_path)

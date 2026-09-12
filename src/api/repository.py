import json
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd


class AnalyticsRepository:
    def __init__(self, duckdb_path: Path, data_dir: Path) -> None:
        self.duckdb_path = duckdb_path
        self.data_dir = data_dir

    def _query(self, sql: str, params: list[Any] | None = None) -> pd.DataFrame:
        with duckdb.connect(str(self.duckdb_path), read_only=True) as connection:
            return connection.execute(sql, params or []).fetchdf()

    def marketplace_overview(self) -> list[dict[str, Any]]:
        frame = self._query(
            """
            select *
            from main_marts.mart_marketplace_overview
            order by snapshot_date_key desc
            """
        )
        return _records(frame)

    def category_metrics(self, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        total = self._query("select count(*) as total from main_marts.mart_category_metrics").loc[0, "total"]
        frame = self._query(
            """
            select *
            from main_marts.mart_category_metrics
            order by catalog_coverage_score desc, category_id
            limit ? offset ?
            """,
            [limit, offset],
        )
        return _records(frame), int(total)

    def category_metric(self, category_id: str) -> dict[str, Any] | None:
        frame = self._query(
            """
            select *
            from main_marts.mart_category_metrics
            where category_id = ?
            """,
            [category_id],
        )
        records = _records(frame)
        return records[0] if records else None

    def seller_item_metrics(self, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        try:
            total = self._query("select count(*) as total from main_marts.mart_seller_item_metrics").loc[
                0, "total"
            ]
            frame = self._query(
                """
                select *
                from main_marts.mart_seller_item_metrics
                order by item_count desc, seller_id, category_id, status
                limit ? offset ?
                """,
                [limit, offset],
            )
            return _records(frame), int(total)
        except duckdb.Error:
            return self._seller_item_metrics_from_parquet(limit=limit, offset=offset)

    def _seller_item_metrics_from_parquet(
        self,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        path = self.data_dir / "gold" / "seller_item_metrics.parquet"
        if not path.exists():
            return [], 0
        frame = pd.read_parquet(path).sort_values(
            ["item_count", "seller_id", "category_id", "status"],
            ascending=[False, True, True, True],
        )
        total = len(frame)
        return _records(frame.iloc[offset : offset + limit]), total

    def seller_items(
        self,
        limit: int,
        offset: int,
        seller_id: str | None = None,
        category_id: str | None = None,
        status: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        filters, params = _seller_item_filters(seller_id=seller_id, category_id=category_id, status=status)
        where_clause = f"where {' and '.join(filters)}" if filters else ""
        try:
            total = self._query(
                f"select count(*) as total from main_marts.mart_seller_items {where_clause}",
                params,
            ).loc[0, "total"]
            frame = self._query(
                f"""
                select *
                from main_marts.mart_seller_items
                {where_clause}
                order by snapshot_date_key desc, item_id
                limit ? offset ?
                """,
                [*params, limit, offset],
            )
            return _records(frame), int(total)
        except duckdb.Error:
            return self._seller_items_from_parquet(
                limit=limit,
                offset=offset,
                seller_id=seller_id,
                category_id=category_id,
                status=status,
            )

    def _seller_items_from_parquet(
        self,
        limit: int,
        offset: int,
        seller_id: str | None = None,
        category_id: str | None = None,
        status: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        path = self.data_dir / "silver" / "item_details.parquet"
        if not path.exists():
            return [], 0
        frame = pd.read_parquet(path).rename(columns={"ingested_at": "snapshot_date"})
        if "snapshot_date_key" not in frame.columns and "snapshot_date" in frame.columns:
            frame["snapshot_date_key"] = pd.to_datetime(
                frame["snapshot_date"], utc=True, errors="coerce"
            ).dt.strftime("%Y%m%d").astype("Int64")
        if seller_id:
            frame = frame[frame["seller_id"].astype("string") == seller_id]
        if category_id:
            frame = frame[frame["category_id"].astype("string") == category_id]
        if status:
            frame = frame[frame["status"].astype("string") == status]
        frame = frame.sort_values(["snapshot_date_key", "item_id"], ascending=[False, True])
        total = len(frame)
        columns = [
            "item_id",
            "title",
            "seller_id",
            "category_id",
            "status",
            "condition",
            "listing_type_id",
            "permalink",
            "price",
            "available_quantity",
            "sold_quantity",
            "snapshot_date_key",
            "snapshot_date",
        ]
        return _records(frame[[column for column in columns if column in frame]].iloc[offset : offset + limit]), total

    def ml_scores(self, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        path = self.data_dir / "gold" / "ml_category_scores.parquet"
        frame = pd.read_parquet(path).sort_values(["opportunity_rank", "category_id"])
        total = len(frame)
        return _records(frame.iloc[offset : offset + limit]), total

    def anomalies(self) -> list[dict[str, Any]]:
        path = self.data_dir / "gold" / "ml_category_scores.parquet"
        frame = pd.read_parquet(path)
        return _records(frame[frame["is_anomaly"]].sort_values("anomaly_score", ascending=False))

    def ml_metadata(self) -> dict[str, Any]:
        path = self.data_dir / "gold" / "ml_model_metadata.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def advanced_ml_metadata(self) -> dict[str, Any]:
        path = self.data_dir / "gold" / "ml_advanced_metadata.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def pipeline_runs(self, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        manifests = self._pipeline_manifest_paths()
        total = len(manifests)
        runs = [self._pipeline_run_summary(path) for path in manifests[offset : offset + limit]]
        return runs, total

    def pipeline_run(self, run_id: str) -> dict[str, Any] | None:
        for path in self._pipeline_manifest_paths():
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("run_id") == run_id:
                return payload
        return None

    def latest_pipeline_run(self) -> dict[str, Any] | None:
        manifests = self._pipeline_manifest_paths()
        if not manifests:
            return None
        return json.loads(manifests[0].read_text(encoding="utf-8"))

    def pipeline_observability(self) -> dict[str, Any]:
        path = self.data_dir / "gold" / "pipeline_observability.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def price_history(self, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        path = self.data_dir / "gold" / "price_history.parquet"
        if not path.exists():
            return [], 0
        frame = pd.read_parquet(path).sort_values(
            ["snapshot_date_key", "item_id"],
            ascending=[False, True],
        )
        total = len(frame)
        return _records(frame.iloc[offset : offset + limit]), total

    def _pipeline_manifest_paths(self) -> list[Path]:
        path = self.data_dir / "pipeline_runs"
        return sorted(path.glob("*.json"), key=lambda manifest: manifest.stat().st_mtime, reverse=True)

    def _pipeline_run_summary(self, path: Path) -> dict[str, Any]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        tasks = payload.get("tasks", {})
        task_statuses = {
            task_name: task_payload.get("status", "success")
            for task_name, task_payload in tasks.items()
            if isinstance(task_payload, dict)
        }
        return {
            "run_id": payload.get("run_id"),
            "status": payload.get("status"),
            "query": payload.get("query"),
            "started_at": payload.get("started_at"),
            "finished_at": payload.get("finished_at"),
            "duration_seconds": payload.get("duration_seconds"),
            "task_count": len(tasks) if isinstance(tasks, dict) else 0,
            "task_statuses": task_statuses,
            "manifest_path": str(path),
        }


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    clean = frame.where(pd.notna(frame), None)
    records = clean.to_dict(orient="records")
    for record in records:
        for key, value in list(record.items()):
            if isinstance(value, pd.Timestamp):
                record[key] = value.isoformat()
    return records


def _seller_item_filters(
    seller_id: str | None,
    category_id: str | None,
    status: str | None,
) -> tuple[list[str], list[Any]]:
    filters: list[str] = []
    params: list[Any] = []
    if seller_id:
        filters.append("seller_id = ?")
        params.append(seller_id)
    if category_id:
        filters.append("category_id = ?")
        params.append(category_id)
    if status:
        filters.append("status = ?")
        params.append(status)
    return filters, params

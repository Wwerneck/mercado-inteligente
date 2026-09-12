import duckdb
import pandas as pd

from src.api.repository import AnalyticsRepository
from src.orchestration.pipeline_tasks import write_manifest


def test_seller_item_metrics_falls_back_to_gold_parquet_sorted_by_item_count(tmp_path):
    gold_dir = tmp_path / "gold"
    gold_dir.mkdir()
    pd.DataFrame(
        [
            {
                "seller_id": "123",
                "category_id": "B",
                "status": "active",
                "item_count": 1,
                "active_item_count": 1,
                "avg_price": 10,
                "min_price": 10,
                "max_price": 10,
                "total_available_quantity": 2,
                "total_sold_quantity": 1,
                "latest_ingestion_at": pd.Timestamp("2026-09-10T10:00:00Z"),
            },
            {
                "seller_id": "123",
                "category_id": "A",
                "status": "active",
                "item_count": 2,
                "active_item_count": 2,
                "avg_price": 20,
                "min_price": 10,
                "max_price": 30,
                "total_available_quantity": 5,
                "total_sold_quantity": 3,
                "latest_ingestion_at": pd.Timestamp("2026-09-10T11:00:00Z"),
            },
        ]
    ).to_parquet(gold_dir / "seller_item_metrics.parquet")
    repository = AnalyticsRepository(tmp_path / "missing.duckdb", tmp_path)

    items, total = repository.seller_item_metrics(limit=10, offset=0)

    assert total == 2
    assert items[0]["category_id"] == "A"
    assert items[0]["latest_ingestion_at"] == "2026-09-10T11:00:00+00:00"


def test_seller_item_metrics_prefers_duckdb_mart(tmp_path):
    db_path = tmp_path / "warehouse.duckdb"
    with duckdb.connect(str(db_path)) as connection:
        connection.execute("create schema main_marts")
        connection.execute(
            """
            create table main_marts.mart_seller_item_metrics as
            select
                '123' as seller_id,
                'MLB1' as category_id,
                'active' as status,
                3 as item_count,
                3 as active_item_count,
                20.5 as avg_price,
                10.0 as min_price,
                30.0 as max_price,
                8 as total_available_quantity,
                4 as total_sold_quantity,
                timestamp '2026-09-10 11:00:00' as latest_ingestion_at
            """
        )
    repository = AnalyticsRepository(db_path, tmp_path)

    items, total = repository.seller_item_metrics(limit=10, offset=0)

    assert total == 1
    assert items[0]["item_count"] == 3
    assert items[0]["category_id"] == "MLB1"


def test_seller_items_prefers_duckdb_mart_with_filters(tmp_path):
    db_path = tmp_path / "warehouse.duckdb"
    with duckdb.connect(str(db_path)) as connection:
        connection.execute("create schema main_marts")
        connection.execute(
            """
            create table main_marts.mart_seller_items as
            select
                'MLB1' as item_id,
                'Notebook' as title,
                '123' as seller_id,
                'MLB1652' as category_id,
                'active' as status,
                'new' as condition,
                'gold_special' as listing_type_id,
                'https://example.com/MLB1' as permalink,
                100.0 as price,
                5 as available_quantity,
                2 as sold_quantity,
                20260910 as snapshot_date_key,
                '2026-09-10' as snapshot_date
            union all
            select
                'MLB2', 'Phone', '123', 'MLB1055', 'paused', 'used',
                'gold_special', 'https://example.com/MLB2', 50.0, 1, 0, 20260910, '2026-09-10'
            """
        )
    repository = AnalyticsRepository(db_path, tmp_path)

    items, total = repository.seller_items(limit=10, offset=0, status="active")

    assert total == 1
    assert items[0]["item_id"] == "MLB1"


def test_seller_items_falls_back_to_silver_parquet(tmp_path):
    silver_dir = tmp_path / "silver"
    silver_dir.mkdir()
    pd.DataFrame(
        [
            {
                "item_id": "MLB1",
                "title": "Notebook",
                "seller_id": "123",
                "category_id": "MLB1652",
                "status": "active",
                "condition": "new",
                "listing_type_id": "gold_special",
                "permalink": "https://example.com/MLB1",
                "price": 100.0,
                "available_quantity": 5,
                "sold_quantity": 2,
                "ingested_at": pd.Timestamp("2026-09-10T10:00:00Z"),
            }
        ]
    ).to_parquet(silver_dir / "item_details.parquet")
    repository = AnalyticsRepository(tmp_path / "missing.duckdb", tmp_path)

    items, total = repository.seller_items(limit=10, offset=0, category_id="MLB1652")

    assert total == 1
    assert items[0]["item_id"] == "MLB1"


def test_pipeline_runs_returns_latest_manifest_summaries(tmp_path):
    write_manifest(
        tmp_path,
        "run-1",
        {
            "run_id": "run-1",
            "status": "success",
            "query": "notebook",
            "tasks": {
                "extract_marketplace_data": [{"rows": 2}],
                "extract_authenticated_marketplace_data": {"status": "skipped"},
            },
        },
    )
    repository = AnalyticsRepository(tmp_path / "missing.duckdb", tmp_path)

    runs, total = repository.pipeline_runs(limit=10, offset=0)

    assert total == 1
    assert runs[0]["run_id"] == "run-1"
    assert runs[0]["task_count"] == 2
    assert runs[0]["task_statuses"]["extract_authenticated_marketplace_data"] == "skipped"


def test_pipeline_run_returns_manifest_by_run_id(tmp_path):
    write_manifest(tmp_path, "run-1", {"run_id": "run-1", "status": "success", "tasks": {}})
    repository = AnalyticsRepository(tmp_path / "missing.duckdb", tmp_path)

    assert repository.pipeline_run("run-1")["status"] == "success"
    assert repository.pipeline_run("missing") is None

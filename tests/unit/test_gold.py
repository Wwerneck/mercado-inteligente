from pathlib import Path

import pandas as pd

from src.analytics.gold import (
    build_category_metrics,
    build_gold,
    build_marketplace_overview,
    build_price_history,
    build_public_query_metrics,
    build_seller_item_metrics,
)


def test_build_category_metrics_uses_numpy_score():
    categories = pd.DataFrame(
        [
            {
                "category_id": "A",
                "category_name": "A",
                "total_items_in_this_category": 50,
                "children_categories_count": 2,
                "path_from_root": "Root > A",
            },
            {
                "category_id": "B",
                "category_name": "B",
                "total_items_in_this_category": 100,
                "children_categories_count": 0,
                "path_from_root": "Root > B",
            },
        ]
    )
    domains = pd.DataFrame(
        [
            {"domain_id": "D1", "category_id": "A"},
            {"domain_id": "D2", "category_id": "A"},
        ]
    )

    metrics = build_category_metrics(categories, domains)

    assert metrics.iloc[0]["category_id"] == "B"
    assert metrics.loc[metrics["category_id"] == "B", "catalog_coverage_score"].iloc[0] == 100
    assert metrics.loc[metrics["category_id"] == "A", "domain_count"].iloc[0] == 2


def test_build_marketplace_overview_returns_single_row():
    categories = pd.DataFrame(
        [
            {
                "category_id": "A",
                "total_items_in_this_category": 10,
                "children_categories_count": 2,
                "ingested_at": pd.Timestamp("2026-09-10T10:00:00Z"),
            }
        ]
    )
    domains = pd.DataFrame(
        [{"domain_id": "D1", "ingested_at": pd.Timestamp("2026-09-10T11:00:00Z")}]
    )

    overview = build_marketplace_overview(categories, domains)

    assert overview.loc[0, "total_categories"] == 1
    assert overview.loc[0, "total_domains"] == 1


def test_build_public_query_metrics_groups_by_search_query():
    categories = pd.DataFrame(
        [
            {
                "category_id": "A",
                "total_items_in_this_category": 10,
                "ingested_at": pd.Timestamp("2026-09-10T10:00:00Z"),
            },
            {
                "category_id": "B",
                "total_items_in_this_category": 20,
                "ingested_at": pd.Timestamp("2026-09-10T11:00:00Z"),
            },
        ]
    )
    domains = pd.DataFrame(
        [
            {"domain_id": "D1", "category_id": "A", "search_query": "notebook"},
            {"domain_id": "D2", "category_id": "B", "search_query": "notebook"},
            {"domain_id": "D3", "category_id": "B", "search_query": "celular"},
        ]
    )

    metrics = build_public_query_metrics(categories, domains)
    notebook = metrics[metrics["search_query"] == "notebook"].iloc[0]

    assert notebook["category_count"] == 2
    assert notebook["domain_count"] == 2
    assert notebook["total_items_in_categories"] == 30


def test_build_seller_item_metrics_aggregates_by_seller_category_and_status():
    item_details = pd.DataFrame(
        [
            {
                "item_id": "MLB1",
                "seller_id": "123",
                "category_id": "MLB1652",
                "status": "active",
                "price": 100,
                "available_quantity": 5,
                "sold_quantity": 2,
                "ingested_at": pd.Timestamp("2026-09-10T10:00:00Z"),
            },
            {
                "item_id": "MLB2",
                "seller_id": "123",
                "category_id": "MLB1652",
                "status": "active",
                "price": 200,
                "available_quantity": 7,
                "sold_quantity": 3,
                "ingested_at": pd.Timestamp("2026-09-10T11:00:00Z"),
            },
            {
                "item_id": "MLB3",
                "seller_id": "123",
                "category_id": "MLB1652",
                "status": "paused",
                "price": 50,
                "available_quantity": 1,
                "sold_quantity": 0,
                "ingested_at": pd.Timestamp("2026-09-10T12:00:00Z"),
            },
        ]
    )

    metrics = build_seller_item_metrics(item_details)
    active = metrics[metrics["status"] == "active"].iloc[0]

    assert active["item_count"] == 2
    assert active["active_item_count"] == 2
    assert active["avg_price"] == 150
    assert active["total_available_quantity"] == 12
    assert active["total_sold_quantity"] == 5
    assert active["sell_through_rate"] == 29.41
    assert active["price_spread"] == 100
    assert active["paused_item_count"] == 0
    assert active["zero_sales_stock_count"] == 0


def test_build_price_history_calculates_deltas_by_item():
    snapshots = pd.DataFrame(
        [
            {
                "item_id": "MLB1",
                "seller_id": "123",
                "category_id": "A",
                "snapshot_date_key": 20260910,
                "snapshot_date": pd.Timestamp("2026-09-10T10:00:00Z"),
                "price": 100,
                "base_price": 100,
                "original_price": None,
                "currency_id": "BRL",
                "available_quantity": 5,
                "sold_quantity": 2,
                "status": "active",
            },
            {
                "item_id": "MLB1",
                "seller_id": "123",
                "category_id": "A",
                "snapshot_date_key": 20260911,
                "snapshot_date": pd.Timestamp("2026-09-11T10:00:00Z"),
                "price": 90,
                "base_price": 90,
                "original_price": None,
                "currency_id": "BRL",
                "available_quantity": 4,
                "sold_quantity": 3,
                "status": "active",
            },
        ]
    )

    history = build_price_history(snapshots)

    latest = history.iloc[1]
    assert latest["price_change_abs"] == -10
    assert latest["price_change_pct"] == -10
    assert latest["stock_change"] == -1
    assert latest["sold_change"] == 1


def test_build_gold_writes_seller_item_metrics_when_silver_exists(tmp_path):
    silver_dir = tmp_path / "silver"
    silver_dir.mkdir()
    pd.DataFrame(
        [
            {
                "category_id": "A",
                "category_name": "A",
                "total_items_in_this_category": 10,
                "children_categories_count": 0,
                "path_from_root": "Root > A",
                "ingested_at": pd.Timestamp("2026-09-10T10:00:00Z"),
            }
        ]
    ).to_parquet(silver_dir / "categories.parquet")
    pd.DataFrame(
        [{"domain_id": "D1", "category_id": "A", "ingested_at": pd.Timestamp("2026-09-10T10:00:00Z")}]
    ).to_parquet(silver_dir / "domain_discovery.parquet")
    pd.DataFrame(
        [
            {
                "item_id": "MLB1",
                "seller_id": "123",
                "category_id": "A",
                "status": "active",
                "price": 100,
                "available_quantity": 5,
                "sold_quantity": 2,
                "ingested_at": pd.Timestamp("2026-09-10T10:00:00Z"),
            }
        ]
    ).to_parquet(silver_dir / "item_details.parquet")
    pd.DataFrame(
        [
            {
                "item_id": "MLB1",
                "seller_id": "123",
                "category_id": "A",
                "snapshot_date_key": 20260910,
                "snapshot_date": pd.Timestamp("2026-09-10T10:00:00Z"),
                "price": 100,
                "base_price": 100,
                "original_price": None,
                "currency_id": "BRL",
                "available_quantity": 5,
                "sold_quantity": 2,
                "status": "active",
            }
        ]
    ).to_parquet(silver_dir / "item_price_snapshots.parquet")

    outputs = build_gold(tmp_path)

    assert Path(outputs["seller_item_metrics"]).exists()
    assert Path(outputs["price_history"]).exists()
    metrics = pd.read_parquet(outputs["seller_item_metrics"])
    assert metrics.loc[0, "seller_id"] == "123"

from pathlib import Path

import duckdb
import pandas as pd

from src.database.dimensional import DimensionalModel
from src.database.duckdb_repository import load_dimensional_model


def test_load_dimensional_model_to_duckdb(tmp_path: Path):
    model = DimensionalModel(
        dim_category=pd.DataFrame(
            [
                {
                    "category_id": "MLB1652",
                    "category_name": "Notebooks",
                    "path_from_root": "Informatica > Notebooks",
                    "attribute_types": "variations",
                    "settings_adult_content": False,
                }
            ]
        ),
        dim_domain=pd.DataFrame(
            [
                {
                    "domain_category_id": "MLB-NOTEBOOKS__MLB1652",
                    "domain_id": "MLB-NOTEBOOKS",
                    "domain_name": "Notebooks",
                    "category_id": "MLB1652",
                    "category_name": "Notebooks",
                    "search_query": "notebook",
                }
            ]
        ),
        dim_seller=pd.DataFrame([{"seller_id": "123"}]),
        dim_item=pd.DataFrame(
            [
                {
                    "item_id": "MLB1",
                    "title": "Notebook",
                    "category_id": "MLB1652",
                    "seller_id": "123",
                    "condition": "new",
                    "listing_type_id": "gold_special",
                    "permalink": "https://produto.mercadolivre.com.br/MLB1",
                }
            ]
        ),
        dim_date=pd.DataFrame([{"date_key": 20260910, "date": "2026-09-10", "year": 2026, "month": 9, "day": 10}]),
        fact_category_snapshot=pd.DataFrame(
            [
                {
                    "category_id": "MLB1652",
                    "snapshot_date_key": 20260910,
                    "domain_count": 1,
                    "total_items_in_this_category": 100,
                    "children_categories_count": 0,
                    "category_depth": 2,
                    "catalog_coverage_score": 100.0,
                }
            ]
        ),
        fact_marketplace_overview=pd.DataFrame(
            [
                {
                    "snapshot_date_key": 20260910,
                    "total_categories": 1,
                    "total_domains": 1,
                    "total_items_in_categories": 100,
                    "avg_children_categories": 0.0,
                    "latest_ingestion_at": pd.Timestamp("2026-09-10T10:00:00Z"),
                }
            ]
        ),
        fact_seller_item_snapshot=pd.DataFrame(
            [
                {
                    "item_id": "MLB1",
                    "snapshot_date_key": 20260910,
                    "price": 2500.0,
                    "available_quantity": 5,
                    "sold_quantity": 2,
                    "status": "active",
                }
            ]
        ),
    )

    db_path = tmp_path / "warehouse.duckdb"
    counts = load_dimensional_model(db_path, model)

    assert counts["dim_category"] == 1
    assert counts["dim_seller"] == 1
    with duckdb.connect(str(db_path)) as connection:
        total = connection.execute("select count(*) from analytics.fact_category_snapshot").fetchone()[0]
        seller_total = connection.execute("select count(*) from analytics.fact_seller_item_snapshot").fetchone()[0]
    assert total == 1
    assert seller_total == 1

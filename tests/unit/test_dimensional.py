from pathlib import Path

import pandas as pd

from src.database.dimensional import build_dimensional_model


def test_build_dimensional_model_creates_expected_grains(tmp_path: Path):
    silver_dir = tmp_path / "silver"
    gold_dir = tmp_path / "gold"
    silver_dir.mkdir()
    gold_dir.mkdir()

    pd.DataFrame(
        [
            {
                "category_id": "MLB1652",
                "category_name": "Notebooks",
                "picture_url": None,
                "total_items_in_this_category": 100,
                "path_from_root": "Informatica > Notebooks",
                "children_categories_count": 0,
                "attribute_types": "variations",
                "settings_adult_content": False,
                "ingested_at": pd.Timestamp("2026-09-10T10:00:00Z"),
                "source": "mercado_livre",
            }
        ]
    ).to_parquet(silver_dir / "categories.parquet", index=False)
    pd.DataFrame(
        [
            {
                "domain_category_id": "MLB-NOTEBOOKS__MLB1652",
                "domain_id": "MLB-NOTEBOOKS",
                "domain_name": "Notebooks",
                "category_id": "MLB1652",
                "category_name": "Notebooks",
                "search_query": "notebook",
                "ingested_at": pd.Timestamp("2026-09-10T10:00:00Z"),
                "source": "mercado_livre",
            }
        ]
    ).to_parquet(silver_dir / "domain_discovery.parquet", index=False)
    pd.DataFrame(
        [
            {
                "item_id": "MLB1",
                "title": "Notebook",
                "price": 2500.0,
                "currency_id": "BRL",
                "available_quantity": 5,
                "sold_quantity": 2,
                "status": "active",
                "condition": "new",
                "category_id": "MLB1652",
                "listing_type_id": "gold_special",
                "permalink": "https://produto.mercadolivre.com.br/MLB1",
                "seller_id": "123",
                "site_id": "MLB",
                "date_created": pd.Timestamp("2026-09-01T10:00:00Z"),
                "last_updated": pd.Timestamp("2026-09-10T10:00:00Z"),
                "ingested_at": pd.Timestamp("2026-09-10T10:00:00Z"),
                "source": "mercado_livre_oauth",
            }
        ]
    ).to_parquet(silver_dir / "item_details.parquet", index=False)
    pd.DataFrame(
        [
            {
                "category_id": "MLB1652",
                "category_name": "Notebooks",
                "domain_count": 1,
                "total_items_in_this_category": 100,
                "children_categories_count": 0,
                "category_depth": 2,
                "catalog_coverage_score": 100.0,
            }
        ]
    ).to_parquet(gold_dir / "category_metrics.parquet", index=False)
    pd.DataFrame(
        [
            {
                "total_categories": 1,
                "total_domains": 1,
                "total_items_in_categories": 100,
                "avg_children_categories": 0.0,
                "latest_ingestion_at": pd.Timestamp("2026-09-10T10:00:00Z"),
            }
        ]
    ).to_parquet(gold_dir / "marketplace_overview.parquet", index=False)

    model = build_dimensional_model(tmp_path)

    assert len(model.dim_category) == 1
    assert len(model.dim_domain) == 1
    assert model.dim_date.loc[0, "date_key"] == 20260910
    assert len(model.fact_category_snapshot) == 1
    assert len(model.dim_seller) == 1
    assert len(model.dim_item) == 1
    assert len(model.fact_seller_item_snapshot) == 1
    assert model.fact_seller_item_snapshot.loc[0, "snapshot_date_key"] == 20260910

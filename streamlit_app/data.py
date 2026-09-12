import json
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = PROJECT_ROOT / "data" / "warehouse" / "mercado_intelligence.duckdb"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"


def query_duckdb(sql: str) -> pd.DataFrame:
    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as connection:
        return connection.execute(sql).fetchdf()


def load_category_metrics() -> pd.DataFrame:
    return query_duckdb(
        """
        select *
        from main_marts.mart_category_metrics
        order by catalog_coverage_score desc, category_id
        """
    )


def load_marketplace_overview() -> pd.DataFrame:
    return query_duckdb(
        """
        select *
        from main_marts.mart_marketplace_overview
        order by snapshot_date_key desc
        """
    )


def load_ml_scores() -> pd.DataFrame:
    return pd.read_parquet(GOLD_DIR / "ml_category_scores.parquet").sort_values(
        ["opportunity_rank", "category_id"]
    )


def load_public_query_metrics() -> pd.DataFrame:
    path = GOLD_DIR / "public_query_metrics.parquet"
    if not path.exists():
        return pd.DataFrame(
            columns=[
                "search_query",
                "category_count",
                "domain_count",
                "total_items_in_categories",
                "avg_catalog_coverage_score",
                "latest_ingestion_at",
            ]
        )
    return pd.read_parquet(path).sort_values(
        ["domain_count", "category_count", "search_query"],
        ascending=[False, False, True],
    )


def load_ml_metadata() -> dict[str, Any]:
    return json.loads((GOLD_DIR / "ml_model_metadata.json").read_text(encoding="utf-8"))


def load_advanced_ml_metadata() -> dict[str, Any]:
    return json.loads((GOLD_DIR / "ml_advanced_metadata.json").read_text(encoding="utf-8"))

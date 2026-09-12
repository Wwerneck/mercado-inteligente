from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class DimensionalModel:
    dim_category: pd.DataFrame
    dim_domain: pd.DataFrame
    dim_seller: pd.DataFrame
    dim_item: pd.DataFrame
    dim_date: pd.DataFrame
    fact_category_snapshot: pd.DataFrame
    fact_marketplace_overview: pd.DataFrame
    fact_seller_item_snapshot: pd.DataFrame


def _date_key(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True).dt.strftime("%Y%m%d").astype("int64")


def build_dimensional_model(data_dir: Path) -> DimensionalModel:
    categories = pd.read_parquet(data_dir / "silver" / "categories.parquet")
    domains = pd.read_parquet(data_dir / "silver" / "domain_discovery.parquet")
    item_details_path = data_dir / "silver" / "item_details.parquet"
    item_details = pd.read_parquet(item_details_path) if item_details_path.exists() else _empty_item_details()
    category_metrics = pd.read_parquet(data_dir / "gold" / "category_metrics.parquet")
    overview = pd.read_parquet(data_dir / "gold" / "marketplace_overview.parquet")

    dim_category = categories[
        [
            "category_id",
            "category_name",
            "path_from_root",
            "attribute_types",
            "settings_adult_content",
        ]
    ].drop_duplicates("category_id")

    dim_domain = domains[
        ["domain_category_id", "domain_id", "domain_name", "category_id", "category_name", "search_query"]
    ].drop_duplicates("domain_category_id")

    dim_seller = (
        item_details[["seller_id"]]
        .dropna(subset=["seller_id"])
        .drop_duplicates("seller_id")
        .reset_index(drop=True)
        if not item_details.empty
        else pd.DataFrame(columns=["seller_id"])
    )

    dim_item = (
        item_details[
            [
                "item_id",
                "title",
                "category_id",
                "seller_id",
                "condition",
                "listing_type_id",
                "permalink",
            ]
        ]
        .dropna(subset=["item_id"])
        .drop_duplicates("item_id")
        .reset_index(drop=True)
        if not item_details.empty
        else pd.DataFrame(
            columns=[
                "item_id",
                "title",
                "category_id",
                "seller_id",
                "condition",
                "listing_type_id",
                "permalink",
            ]
        )
    )

    ingestion_dates = pd.concat(
        [
            pd.to_datetime(categories["ingested_at"], utc=True),
            pd.to_datetime(domains["ingested_at"], utc=True),
            pd.to_datetime(item_details["ingested_at"], utc=True),
            pd.to_datetime(overview["latest_ingestion_at"], utc=True),
        ],
        ignore_index=True,
    ).dropna()
    unique_dates = pd.Series(sorted(ingestion_dates.dt.normalize().unique()))
    dim_date = pd.DataFrame(
        {
            "date_key": pd.to_datetime(unique_dates, utc=True).dt.strftime("%Y%m%d").astype("int64"),
            "date": pd.to_datetime(unique_dates, utc=True).dt.date.astype("string"),
            "year": pd.to_datetime(unique_dates, utc=True).dt.year.astype("int64"),
            "month": pd.to_datetime(unique_dates, utc=True).dt.month.astype("int64"),
            "day": pd.to_datetime(unique_dates, utc=True).dt.day.astype("int64"),
        }
    )

    fact_category_snapshot = category_metrics.merge(
        categories[["category_id", "ingested_at"]],
        on="category_id",
        how="left",
    )
    fact_category_snapshot["snapshot_date_key"] = _date_key(fact_category_snapshot["ingested_at"])
    fact_category_snapshot = fact_category_snapshot[
        [
            "category_id",
            "snapshot_date_key",
            "domain_count",
            "total_items_in_this_category",
            "children_categories_count",
            "category_depth",
            "catalog_coverage_score",
        ]
    ]

    fact_marketplace_overview = overview.copy()
    fact_marketplace_overview["snapshot_date_key"] = _date_key(
        fact_marketplace_overview["latest_ingestion_at"]
    )
    fact_marketplace_overview = fact_marketplace_overview[
        [
            "snapshot_date_key",
            "total_categories",
            "total_domains",
            "total_items_in_categories",
            "avg_children_categories",
            "latest_ingestion_at",
        ]
    ]

    fact_seller_item_snapshot = (
        item_details[
            [
                "item_id",
                "ingested_at",
                "price",
                "available_quantity",
                "sold_quantity",
                "status",
            ]
        ]
        .dropna(subset=["item_id", "ingested_at"])
        .copy()
        if not item_details.empty
        else pd.DataFrame(
            columns=[
                "item_id",
                "ingested_at",
                "price",
                "available_quantity",
                "sold_quantity",
                "status",
            ]
        )
    )
    fact_seller_item_snapshot["snapshot_date_key"] = (
        _date_key(fact_seller_item_snapshot["ingested_at"])
        if not fact_seller_item_snapshot.empty
        else pd.Series(dtype="int64")
    )
    fact_seller_item_snapshot = fact_seller_item_snapshot[
        [
            "item_id",
            "snapshot_date_key",
            "price",
            "available_quantity",
            "sold_quantity",
            "status",
        ]
    ]

    return DimensionalModel(
        dim_category=dim_category.reset_index(drop=True),
        dim_domain=dim_domain.reset_index(drop=True),
        dim_seller=dim_seller.reset_index(drop=True),
        dim_item=dim_item.reset_index(drop=True),
        dim_date=dim_date.reset_index(drop=True),
        fact_category_snapshot=fact_category_snapshot.reset_index(drop=True),
        fact_marketplace_overview=fact_marketplace_overview.reset_index(drop=True),
        fact_seller_item_snapshot=fact_seller_item_snapshot.reset_index(drop=True),
    )


def _empty_item_details() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "item_id",
            "title",
            "price",
            "available_quantity",
            "sold_quantity",
            "status",
            "category_id",
            "seller_id",
            "condition",
            "listing_type_id",
            "permalink",
            "ingested_at",
        ]
    )

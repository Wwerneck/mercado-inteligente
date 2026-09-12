from pathlib import Path

import numpy as np
import pandas as pd

from src.storage.lake import write_parquet


def build_category_metrics(categories: pd.DataFrame, domains: pd.DataFrame) -> pd.DataFrame:
    if categories.empty:
        return pd.DataFrame(
            columns=[
                "category_id",
                "category_name",
                "domain_count",
                "total_items_in_this_category",
                "children_categories_count",
                "category_depth",
                "catalog_coverage_score",
            ]
        )

    domain_counts = (
        domains.groupby("category_id", dropna=False)
        .agg(domain_count=("domain_id", "nunique"))
        .reset_index()
        if not domains.empty
        else pd.DataFrame(columns=["category_id", "domain_count"])
    )
    metrics = categories.merge(domain_counts, on="category_id", how="left")
    metrics["domain_count"] = metrics["domain_count"].fillna(0).astype("int64")
    metrics["category_depth"] = metrics["path_from_root"].fillna("").map(
        lambda value: len([part for part in str(value).split(" > ") if part])
    )

    items = metrics["total_items_in_this_category"].fillna(0).to_numpy(dtype=float)
    max_items = float(np.nanmax(items)) if len(items) else 0.0
    if max_items > 0:
        metrics["catalog_coverage_score"] = np.round((items / max_items) * 100, 2)
    else:
        metrics["catalog_coverage_score"] = 0.0

    return metrics[
        [
            "category_id",
            "category_name",
            "domain_count",
            "total_items_in_this_category",
            "children_categories_count",
            "category_depth",
            "catalog_coverage_score",
        ]
    ].sort_values(["catalog_coverage_score", "category_id"], ascending=[False, True])


def build_marketplace_overview(categories: pd.DataFrame, domains: pd.DataFrame) -> pd.DataFrame:
    total_categories = int(categories["category_id"].nunique()) if not categories.empty else 0
    total_domains = int(domains["domain_id"].nunique()) if not domains.empty else 0
    total_items = (
        int(categories["total_items_in_this_category"].fillna(0).sum()) if not categories.empty else 0
    )
    latest_ingestion = max(
        [
            value
            for value in [
                categories["ingested_at"].max() if not categories.empty else pd.NaT,
                domains["ingested_at"].max() if not domains.empty else pd.NaT,
            ]
            if pd.notna(value)
        ],
        default=pd.NaT,
    )
    avg_children = (
        float(np.round(categories["children_categories_count"].mean(), 2))
        if not categories.empty
        else 0.0
    )
    return pd.DataFrame(
        [
            {
                "total_categories": total_categories,
                "total_domains": total_domains,
                "total_items_in_categories": total_items,
                "avg_children_categories": avg_children,
                "latest_ingestion_at": latest_ingestion,
            }
        ]
    )


def build_public_query_metrics(categories: pd.DataFrame, domains: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "search_query",
        "category_count",
        "domain_count",
        "total_items_in_categories",
        "avg_catalog_coverage_score",
        "latest_ingestion_at",
    ]
    if domains.empty:
        return pd.DataFrame(columns=columns)

    domains = domains.copy()
    if "search_query" not in domains:
        domains["search_query"] = "unknown"

    category_lookup = categories[
        ["category_id", "total_items_in_this_category", "ingested_at"]
    ].drop_duplicates("category_id")
    enriched = domains.merge(category_lookup, on="category_id", how="left")
    max_items = enriched["total_items_in_this_category"].fillna(0).max()
    enriched["catalog_coverage_score"] = (
        (enriched["total_items_in_this_category"].fillna(0) / max_items) * 100
        if max_items
        else 0
    )
    ingestion_column = "ingested_at_x" if "ingested_at_x" in enriched else "ingested_at"
    if ingestion_column not in enriched and "ingested_at_y" in enriched:
        ingestion_column = "ingested_at_y"
    enriched["metric_ingested_at"] = pd.to_datetime(
        enriched[ingestion_column], utc=True, errors="coerce"
    )

    metrics = (
        enriched.groupby("search_query", dropna=False)
        .agg(
            category_count=("category_id", "nunique"),
            domain_count=("domain_id", "nunique"),
            total_items_in_categories=("total_items_in_this_category", "sum"),
            avg_catalog_coverage_score=("catalog_coverage_score", "mean"),
            latest_ingestion_at=("metric_ingested_at", "max"),
        )
        .reset_index()
    )
    metrics["category_count"] = metrics["category_count"].astype("int64")
    metrics["domain_count"] = metrics["domain_count"].astype("int64")
    metrics["total_items_in_categories"] = (
        metrics["total_items_in_categories"].fillna(0).astype("int64")
    )
    metrics["avg_catalog_coverage_score"] = metrics["avg_catalog_coverage_score"].round(2)
    return metrics[columns].sort_values(
        ["domain_count", "category_count", "search_query"], ascending=[False, False, True]
    )


def build_seller_item_metrics(item_details: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "seller_id",
        "category_id",
        "status",
        "item_count",
        "active_item_count",
        "avg_price",
        "min_price",
        "max_price",
        "total_available_quantity",
        "total_sold_quantity",
        "sell_through_rate",
        "price_spread",
        "paused_item_count",
        "zero_sales_stock_count",
        "latest_ingestion_at",
    ]
    if item_details.empty:
        return pd.DataFrame(columns=columns)

    items = item_details.copy()
    items["seller_id"] = items["seller_id"].astype("string")
    items["category_id"] = items["category_id"].astype("string")
    items["status"] = items["status"].astype("string").fillna("unknown")
    items["price"] = pd.to_numeric(items["price"], errors="coerce")
    items["available_quantity"] = pd.to_numeric(items["available_quantity"], errors="coerce").fillna(0)
    items["sold_quantity"] = pd.to_numeric(items["sold_quantity"], errors="coerce").fillna(0)
    items["is_active"] = items["status"].eq("active").astype("int64")
    items["is_paused"] = items["status"].eq("paused").astype("int64")
    items["has_stock_without_sales"] = (
        items["available_quantity"].gt(0) & items["sold_quantity"].eq(0)
    ).astype("int64")
    items["ingested_at"] = pd.to_datetime(items["ingested_at"], utc=True, errors="coerce")

    metrics = (
        items.groupby(["seller_id", "category_id", "status"], dropna=False)
        .agg(
            item_count=("item_id", "nunique"),
            active_item_count=("is_active", "sum"),
            avg_price=("price", "mean"),
            min_price=("price", "min"),
            max_price=("price", "max"),
            total_available_quantity=("available_quantity", "sum"),
            total_sold_quantity=("sold_quantity", "sum"),
            paused_item_count=("is_paused", "sum"),
            zero_sales_stock_count=("has_stock_without_sales", "sum"),
            latest_ingestion_at=("ingested_at", "max"),
        )
        .reset_index()
    )
    metrics["active_item_count"] = metrics["active_item_count"].astype("int64")
    metrics["avg_price"] = metrics["avg_price"].round(2)
    metrics["total_available_quantity"] = metrics["total_available_quantity"].astype("int64")
    metrics["total_sold_quantity"] = metrics["total_sold_quantity"].astype("int64")
    inventory_denominator = metrics["total_available_quantity"] + metrics["total_sold_quantity"]
    metrics["sell_through_rate"] = np.where(
        inventory_denominator > 0,
        (metrics["total_sold_quantity"] / inventory_denominator) * 100,
        0,
    ).round(2)
    metrics["price_spread"] = (metrics["max_price"] - metrics["min_price"]).round(2)
    metrics["paused_item_count"] = metrics["paused_item_count"].astype("int64")
    metrics["zero_sales_stock_count"] = metrics["zero_sales_stock_count"].astype("int64")

    return metrics[columns].sort_values(
        ["item_count", "seller_id", "category_id", "status"],
        ascending=[False, True, True, True],
    )


def build_price_history(item_price_snapshots: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "item_id",
        "seller_id",
        "category_id",
        "snapshot_date_key",
        "snapshot_date",
        "price",
        "base_price",
        "original_price",
        "currency_id",
        "available_quantity",
        "sold_quantity",
        "status",
        "price_change_abs",
        "price_change_pct",
        "stock_change",
        "sold_change",
    ]
    if item_price_snapshots.empty:
        return pd.DataFrame(columns=columns)

    snapshots = item_price_snapshots.copy()
    snapshots["snapshot_date"] = pd.to_datetime(
        snapshots["snapshot_date"], utc=True, errors="coerce"
    )
    for column in ["price", "base_price", "original_price", "available_quantity", "sold_quantity"]:
        snapshots[column] = pd.to_numeric(snapshots[column], errors="coerce")
    snapshots = snapshots.sort_values(["item_id", "snapshot_date"])
    previous_price = snapshots.groupby("item_id")["price"].shift(1)
    snapshots["price_change_abs"] = (snapshots["price"] - previous_price).round(2)
    snapshots["price_change_pct"] = np.where(
        previous_price > 0,
        ((snapshots["price"] - previous_price) / previous_price) * 100,
        np.nan,
    )
    snapshots["price_change_pct"] = snapshots["price_change_pct"].round(2)
    snapshots["stock_change"] = (
        snapshots["available_quantity"]
        - snapshots.groupby("item_id")["available_quantity"].shift(1)
    )
    snapshots["sold_change"] = (
        snapshots["sold_quantity"] - snapshots.groupby("item_id")["sold_quantity"].shift(1)
    )
    return snapshots[columns].reset_index(drop=True)


def build_gold(data_dir: Path) -> dict[str, str]:
    categories = pd.read_parquet(data_dir / "silver" / "categories.parquet")
    domains = pd.read_parquet(data_dir / "silver" / "domain_discovery.parquet")
    item_details_path = data_dir / "silver" / "item_details.parquet"
    item_details = pd.read_parquet(item_details_path) if item_details_path.exists() else pd.DataFrame()
    item_prices_path = data_dir / "silver" / "item_price_snapshots.parquet"
    item_prices = pd.read_parquet(item_prices_path) if item_prices_path.exists() else pd.DataFrame()

    category_metrics = build_category_metrics(categories, domains)
    overview = build_marketplace_overview(categories, domains)
    public_query_metrics = build_public_query_metrics(categories, domains)
    seller_item_metrics = build_seller_item_metrics(item_details)
    price_history = build_price_history(item_prices)

    return {
        "category_metrics": str(
            write_parquet(category_metrics, data_dir / "gold" / "category_metrics.parquet")
        ),
        "marketplace_overview": str(
            write_parquet(overview, data_dir / "gold" / "marketplace_overview.parquet")
        ),
        "public_query_metrics": str(
            write_parquet(public_query_metrics, data_dir / "gold" / "public_query_metrics.parquet")
        ),
        "seller_item_metrics": str(
            write_parquet(seller_item_metrics, data_dir / "gold" / "seller_item_metrics.parquet")
        ),
        "price_history": str(
            write_parquet(price_history, data_dir / "gold" / "price_history.parquet")
        ),
    }

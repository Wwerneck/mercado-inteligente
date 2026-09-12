import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import pandas as pd

from src.storage.lake import read_parquet_dataset, write_parquet
from src.validation.data_quality import (
    raise_on_failed_checks,
    require_columns,
    require_non_null,
    require_unique,
)


def _parse_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    return {}


def _latest_by_record_id(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    frame = frame.copy()
    frame["ingested_at"] = pd.to_datetime(frame["ingested_at"], utc=True, errors="coerce")
    frame = frame.sort_values("ingested_at")
    return frame.drop_duplicates(subset=["record_id"], keep="last").reset_index(drop=True)


def _normalized_column(normalized: pd.DataFrame, name: str) -> pd.Series:
    if name in normalized:
        return normalized[name]
    return pd.Series([None] * len(normalized))


def transform_domain_discovery(bronze: pd.DataFrame) -> pd.DataFrame:
    if bronze.empty:
        return pd.DataFrame(
            columns=[
                "query_domain_category_id",
                "domain_id",
                "domain_category_id",
                "domain_name",
                "category_id",
                "category_name",
                "search_query",
                "ingested_at",
                "source",
            ]
        )

    normalized = pd.json_normalize(bronze["payload"].map(_parse_payload))
    silver = pd.DataFrame(
        {
            "domain_id": normalized.get("domain_id"),
            "domain_name": normalized.get("domain_name"),
            "category_id": normalized.get("category_id"),
            "category_name": normalized.get("category_name"),
            "search_query": bronze.get("endpoint", pd.Series([None] * len(bronze))).map(
                _extract_query_from_endpoint
            ),
            "ingested_at": pd.to_datetime(bronze["ingested_at"], utc=True, errors="coerce"),
            "source": bronze["source"].astype("string"),
        }
    )
    silver["domain_category_id"] = silver["domain_id"].astype("string") + "__" + silver[
        "category_id"
    ].astype("string")
    silver["query_domain_category_id"] = (
        silver["search_query"].astype("string")
        + "__"
        + silver["domain_category_id"].astype("string")
    )
    silver = silver.sort_values("ingested_at").drop_duplicates(
        subset=["query_domain_category_id"], keep="last"
    ).reset_index(drop=True)
    checks = [
        require_columns(
            silver,
            [
                "query_domain_category_id",
                "domain_category_id",
                "domain_id",
                "category_id",
                "ingested_at",
            ],
            "silver_domain_discovery",
        ),
        require_non_null(
            silver,
            [
                "query_domain_category_id",
                "domain_category_id",
                "domain_id",
                "category_id",
                "ingested_at",
            ],
            "silver_domain_discovery",
        ),
        require_unique(silver, "query_domain_category_id", "silver_domain_discovery"),
    ]
    raise_on_failed_checks(checks)
    return silver[
        [
            "domain_category_id",
            "query_domain_category_id",
            "domain_id",
            "domain_name",
            "category_id",
            "category_name",
            "search_query",
            "ingested_at",
            "source",
        ]
    ]


def _extract_query_from_endpoint(endpoint: str | None) -> str | None:
    if not endpoint:
        return None
    parsed = urlparse(endpoint)
    values = parse_qs(parsed.query).get("q")
    return values[0] if values else None


def transform_categories(bronze: pd.DataFrame) -> pd.DataFrame:
    if bronze.empty:
        return pd.DataFrame(
            columns=[
                "category_id",
                "category_name",
                "picture_url",
                "total_items_in_this_category",
                "path_from_root",
                "children_categories_count",
                "attribute_types",
                "settings_adult_content",
                "ingested_at",
                "source",
            ]
        )

    latest = _latest_by_record_id(bronze)
    normalized = pd.json_normalize(latest["payload"].map(_parse_payload))
    path_from_root = normalized.get("path_from_root", pd.Series([[]] * len(latest))).map(
        lambda values: " > ".join(item.get("name", "") for item in values) if isinstance(values, list) else ""
    )
    children_count = normalized.get("children_categories", pd.Series([[]] * len(latest))).map(
        lambda values: len(values) if isinstance(values, list) else 0
    )

    silver = pd.DataFrame(
        {
            "category_id": normalized.get("id"),
            "category_name": normalized.get("name"),
            "picture_url": normalized.get("picture"),
            "total_items_in_this_category": pd.to_numeric(
                normalized.get("total_items_in_this_category"), errors="coerce"
            ).astype("Int64"),
            "path_from_root": path_from_root.astype("string"),
            "children_categories_count": children_count.astype("int64"),
            "attribute_types": normalized.get("attribute_types"),
            "settings_adult_content": normalized.get("settings.adult_content"),
            "ingested_at": latest["ingested_at"],
            "source": latest["source"].astype("string"),
        }
    )
    checks = [
        require_columns(silver, ["category_id", "category_name", "ingested_at"], "silver_categories"),
        require_non_null(silver, ["category_id", "category_name", "ingested_at"], "silver_categories"),
        require_unique(silver, "category_id", "silver_categories"),
    ]
    raise_on_failed_checks(checks)
    return silver.reset_index(drop=True)


def transform_item_details(bronze: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "item_id",
        "title",
        "price",
        "currency_id",
        "available_quantity",
        "sold_quantity",
        "status",
        "condition",
        "category_id",
        "listing_type_id",
        "permalink",
        "seller_id",
        "site_id",
        "date_created",
        "last_updated",
        "ingested_at",
        "source",
    ]
    if bronze.empty:
        return pd.DataFrame(columns=columns)

    latest = _latest_by_record_id(bronze)
    normalized = pd.json_normalize(latest["payload"].map(_parse_payload))
    seller_id = _normalized_column(normalized, "seller_id")
    silver = pd.DataFrame(
        {
            "item_id": _normalized_column(normalized, "id"),
            "title": _normalized_column(normalized, "title"),
            "price": pd.to_numeric(_normalized_column(normalized, "price"), errors="coerce"),
            "currency_id": _normalized_column(normalized, "currency_id"),
            "available_quantity": pd.to_numeric(
                _normalized_column(normalized, "available_quantity"), errors="coerce"
            ).astype("Int64"),
            "sold_quantity": pd.to_numeric(
                _normalized_column(normalized, "sold_quantity"), errors="coerce"
            ).astype("Int64"),
            "status": _normalized_column(normalized, "status"),
            "condition": _normalized_column(normalized, "condition"),
            "category_id": _normalized_column(normalized, "category_id"),
            "listing_type_id": _normalized_column(normalized, "listing_type_id"),
            "permalink": _normalized_column(normalized, "permalink"),
            "seller_id": seller_id.astype("string"),
            "site_id": _normalized_column(normalized, "site_id"),
            "date_created": pd.to_datetime(
                _normalized_column(normalized, "date_created"), utc=True, errors="coerce"
            ),
            "last_updated": pd.to_datetime(
                _normalized_column(normalized, "last_updated"), utc=True, errors="coerce"
            ),
            "ingested_at": latest["ingested_at"],
            "source": latest["source"].astype("string"),
        }
    )
    checks = [
        require_columns(silver, ["item_id", "ingested_at"], "silver_item_details"),
        require_non_null(silver, ["item_id", "ingested_at"], "silver_item_details"),
        require_unique(silver, "item_id", "silver_item_details"),
    ]
    raise_on_failed_checks(checks)
    return silver[columns].reset_index(drop=True)


def transform_item_price_snapshots(bronze: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "item_id",
        "seller_id",
        "category_id",
        "price",
        "base_price",
        "original_price",
        "currency_id",
        "available_quantity",
        "sold_quantity",
        "status",
        "condition",
        "last_updated",
        "snapshot_date",
        "snapshot_date_key",
        "ingested_at",
        "source",
    ]
    if bronze.empty:
        return pd.DataFrame(columns=columns)

    normalized = pd.json_normalize(bronze["payload"].map(_parse_payload))
    snapshot_date = pd.to_datetime(bronze["ingested_at"], utc=True, errors="coerce")
    silver = pd.DataFrame(
        {
            "item_id": _normalized_column(normalized, "item_id").fillna(
                _normalized_column(normalized, "id")
            ),
            "seller_id": _normalized_column(normalized, "seller_id").astype("string"),
            "category_id": _normalized_column(normalized, "category_id").astype("string"),
            "price": pd.to_numeric(_normalized_column(normalized, "price"), errors="coerce"),
            "base_price": pd.to_numeric(
                _normalized_column(normalized, "base_price"), errors="coerce"
            ),
            "original_price": pd.to_numeric(
                _normalized_column(normalized, "original_price"), errors="coerce"
            ),
            "currency_id": _normalized_column(normalized, "currency_id"),
            "available_quantity": pd.to_numeric(
                _normalized_column(normalized, "available_quantity"), errors="coerce"
            ).astype("Int64"),
            "sold_quantity": pd.to_numeric(
                _normalized_column(normalized, "sold_quantity"), errors="coerce"
            ).astype("Int64"),
            "status": _normalized_column(normalized, "status"),
            "condition": _normalized_column(normalized, "condition"),
            "last_updated": pd.to_datetime(
                _normalized_column(normalized, "last_updated"), utc=True, errors="coerce"
            ),
            "snapshot_date": snapshot_date,
            "snapshot_date_key": snapshot_date.dt.strftime("%Y%m%d").astype("Int64"),
            "ingested_at": snapshot_date,
            "source": bronze["source"].astype("string"),
        }
    )
    silver = silver.sort_values("ingested_at").drop_duplicates(
        subset=["item_id", "snapshot_date"], keep="last"
    )
    checks = [
        require_columns(silver, ["item_id", "snapshot_date"], "silver_item_price_snapshots"),
        require_non_null(silver, ["item_id", "snapshot_date"], "silver_item_price_snapshots"),
    ]
    raise_on_failed_checks(checks)
    return silver[columns].reset_index(drop=True)


def transform_item_descriptions(bronze: pd.DataFrame) -> pd.DataFrame:
    columns = ["item_id", "plain_text", "text_length", "ingested_at", "source"]
    if bronze.empty:
        return pd.DataFrame(columns=columns)

    latest = _latest_by_record_id(bronze)
    normalized = pd.json_normalize(latest["payload"].map(_parse_payload))
    plain_text = _normalized_column(normalized, "plain_text").fillna("")
    silver = pd.DataFrame(
        {
            "item_id": _normalized_column(normalized, "id"),
            "plain_text": plain_text,
            "text_length": plain_text.astype("string").str.len().astype("Int64"),
            "ingested_at": latest["ingested_at"],
            "source": latest["source"].astype("string"),
        }
    )
    checks = [
        require_columns(silver, ["item_id", "ingested_at"], "silver_item_descriptions"),
        require_non_null(silver, ["item_id", "ingested_at"], "silver_item_descriptions"),
        require_unique(silver, "item_id", "silver_item_descriptions"),
    ]
    raise_on_failed_checks(checks)
    return silver[columns].reset_index(drop=True)


def build_silver(data_dir: Path) -> dict[str, str]:
    outputs: dict[str, str] = {}
    domain_bronze = read_parquet_dataset(data_dir / "bronze" / "domain_discovery")
    category_bronze = read_parquet_dataset(data_dir / "bronze" / "categories")
    item_details_bronze = read_parquet_dataset(data_dir / "bronze" / "item_details")
    item_prices_bronze = read_parquet_dataset(data_dir / "bronze" / "item_price_snapshots")
    item_descriptions_bronze = read_parquet_dataset(data_dir / "bronze" / "item_descriptions")

    domain_silver = transform_domain_discovery(domain_bronze)
    category_silver = transform_categories(category_bronze)
    item_details_silver = transform_item_details(item_details_bronze)
    item_prices_silver = transform_item_price_snapshots(item_prices_bronze)
    item_descriptions_silver = transform_item_descriptions(item_descriptions_bronze)

    outputs["domain_discovery"] = str(
        write_parquet(domain_silver, data_dir / "silver" / "domain_discovery.parquet")
    )
    outputs["categories"] = str(write_parquet(category_silver, data_dir / "silver" / "categories.parquet"))
    outputs["item_details"] = str(
        write_parquet(item_details_silver, data_dir / "silver" / "item_details.parquet")
    )
    outputs["item_price_snapshots"] = str(
        write_parquet(item_prices_silver, data_dir / "silver" / "item_price_snapshots.parquet")
    )
    outputs["item_descriptions"] = str(
        write_parquet(item_descriptions_silver, data_dir / "silver" / "item_descriptions.parquet")
    )
    return outputs

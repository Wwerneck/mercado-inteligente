from pathlib import Path

import duckdb
import pandas as pd

from src.database.dimensional import DimensionalModel

TABLE_SCHEMAS = {
    "dim_category": """
        create table if not exists analytics.dim_category (
            category_id varchar primary key,
            category_name varchar not null,
            path_from_root varchar,
            attribute_types varchar,
            settings_adult_content boolean
        )
    """,
    "dim_domain": """
        create table if not exists analytics.dim_domain (
            domain_category_id varchar primary key,
            domain_id varchar not null,
            domain_name varchar not null,
            category_id varchar not null,
            category_name varchar,
            search_query varchar
        )
    """,
    "dim_date": """
        create table if not exists analytics.dim_date (
            date_key bigint primary key,
            date varchar not null,
            year bigint not null,
            month bigint not null,
            day bigint not null
        )
    """,
    "dim_seller": """
        create table if not exists analytics.dim_seller (
            seller_id varchar primary key
        )
    """,
    "dim_item": """
        create table if not exists analytics.dim_item (
            item_id varchar primary key,
            title varchar,
            category_id varchar,
            seller_id varchar,
            condition varchar,
            listing_type_id varchar,
            permalink varchar
        )
    """,
    "fact_category_snapshot": """
        create table if not exists analytics.fact_category_snapshot (
            category_id varchar not null,
            snapshot_date_key bigint not null,
            domain_count bigint not null,
            total_items_in_this_category bigint,
            children_categories_count bigint not null,
            category_depth bigint not null,
            catalog_coverage_score double not null
        )
    """,
    "fact_marketplace_overview": """
        create table if not exists analytics.fact_marketplace_overview (
            snapshot_date_key bigint not null,
            total_categories bigint not null,
            total_domains bigint not null,
            total_items_in_categories bigint not null,
            avg_children_categories double not null,
            latest_ingestion_at timestamp
        )
    """,
    "fact_seller_item_snapshot": """
        create table if not exists analytics.fact_seller_item_snapshot (
            item_id varchar not null,
            snapshot_date_key bigint not null,
            price double,
            available_quantity bigint,
            sold_quantity bigint,
            status varchar
        )
    """,
}


def connect_duckdb(path: Path) -> duckdb.DuckDBPyConnection:
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path))


def initialize_duckdb(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute("create schema if not exists analytics")
    for table_name in [
        "fact_marketplace_overview",
        "fact_seller_item_snapshot",
        "fact_category_snapshot",
        "dim_item",
        "dim_seller",
        "dim_domain",
        "dim_date",
        "dim_category",
    ]:
        connection.execute(f"drop table if exists analytics.{table_name}")
    for ddl in TABLE_SCHEMAS.values():
        connection.execute(ddl)


def replace_table(connection: duckdb.DuckDBPyConnection, table_name: str, frame: pd.DataFrame) -> None:
    connection.register("frame_to_load", frame)
    connection.execute(f"delete from analytics.{table_name}")
    connection.execute(f"insert into analytics.{table_name} select * from frame_to_load")
    connection.unregister("frame_to_load")


def load_dimensional_model(path: Path, model: DimensionalModel) -> dict[str, int]:
    with connect_duckdb(path) as connection:
        initialize_duckdb(connection)
        tables = {
            "dim_category": model.dim_category,
            "dim_domain": model.dim_domain,
            "dim_seller": model.dim_seller,
            "dim_item": model.dim_item,
            "dim_date": model.dim_date,
            "fact_category_snapshot": model.fact_category_snapshot,
            "fact_marketplace_overview": model.fact_marketplace_overview,
            "fact_seller_item_snapshot": model.fact_seller_item_snapshot,
        }
        for table_name, frame in tables.items():
            replace_table(connection, table_name, frame)
        return {table_name: len(frame) for table_name, frame in tables.items()}

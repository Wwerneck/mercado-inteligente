from pathlib import Path

from sqlalchemy import create_engine, text

from src.database.dimensional import DimensionalModel

DDL_PATH = Path("sql/postgres_schema.sql")


def load_dimensional_model_to_postgres(dsn: str, model: DimensionalModel) -> dict[str, int]:
    engine = create_engine(dsn)
    with engine.begin() as connection:
        connection.execute(text(DDL_PATH.read_text(encoding="utf-8")))
        tables = {
            "dim_category": model.dim_category,
            "dim_domain": model.dim_domain,
            "dim_date": model.dim_date,
            "fact_category_snapshot": model.fact_category_snapshot,
            "fact_marketplace_overview": model.fact_marketplace_overview,
        }
        for table_name, frame in tables.items():
            connection.execute(text(f"truncate table analytics.{table_name}"))
            frame.to_sql(table_name, connection, schema="analytics", if_exists="append", index=False)
        return {table_name: len(frame) for table_name, frame in tables.items()}


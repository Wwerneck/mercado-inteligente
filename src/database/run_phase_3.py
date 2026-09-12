import argparse
import logging

from src.config.settings import get_settings
from src.database.dimensional import build_dimensional_model
from src.database.duckdb_repository import load_dimensional_model
from src.database.postgres_repository import load_dimensional_model_to_postgres
from src.utils.logging import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fase 3: modelo dimensional em DuckDB/PostgreSQL.")
    parser.add_argument("--postgres", action="store_true", help="Carrega tambem no PostgreSQL via POSTGRES_DSN.")
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level)
    model = build_dimensional_model(settings.data_dir)

    duckdb_counts = load_dimensional_model(settings.duckdb_path, model)
    logger.info(
        "DuckDB dimensional model loaded",
        extra={"pipeline": "phase_3_warehouse", "task": "load_duckdb", "status": "success"},
    )
    print({"database": "duckdb", "path": str(settings.duckdb_path), "rows": duckdb_counts})

    if args.postgres:
        if not settings.postgres_dsn:
            raise ValueError("POSTGRES_DSN must be configured to load PostgreSQL.")
        postgres_counts = load_dimensional_model_to_postgres(settings.postgres_dsn, model)
        logger.info(
            "PostgreSQL dimensional model loaded",
            extra={"pipeline": "phase_3_warehouse", "task": "load_postgres", "status": "success"},
        )
        print({"database": "postgresql", "rows": postgres_counts})


if __name__ == "__main__":
    main()


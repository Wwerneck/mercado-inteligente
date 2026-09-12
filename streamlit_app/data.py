import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = PROJECT_ROOT / "data" / "warehouse" / "mercado_intelligence.duckdb"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
REQUIRED_GOLD_FILES = [
    GOLD_DIR / "ml_category_scores.parquet",
    GOLD_DIR / "ml_model_metadata.json",
    GOLD_DIR / "ml_advanced_metadata.json",
]


def ensure_data_artifacts() -> None:
    if _data_artifacts_ready():
        return

    _run_command([sys.executable, "-m", "src.ingestion.run_batch_collection"])
    _run_command([sys.executable, "-m", "src.processing.run_phase_2"])
    _run_command([sys.executable, "-m", "src.database.run_phase_3"])
    _run_command(_dbt_command("run"), cwd=PROJECT_ROOT / "dbt")
    _run_command(_dbt_command("test"), cwd=PROJECT_ROOT / "dbt")
    _run_command([sys.executable, "-m", "src.ml.run_phase_6"])
    _run_command([sys.executable, "-m", "src.ml.run_phase_7"])

    if not _data_artifacts_ready():
        raise RuntimeError("Bootstrap finalizado, mas os artefatos do dashboard nao foram criados.")


def _data_artifacts_ready() -> bool:
    if not DUCKDB_PATH.exists():
        return False
    if any(not path.exists() for path in REQUIRED_GOLD_FILES):
        return False
    try:
        with duckdb.connect(str(DUCKDB_PATH), read_only=True) as connection:
            connection.execute("select 1 from main_marts.mart_category_metrics limit 1")
            connection.execute("select 1 from main_marts.mart_marketplace_overview limit 1")
    except duckdb.Error:
        return False
    return True


def _dbt_command(command: str) -> list[str]:
    dbt_executable = shutil.which("dbt")
    if dbt_executable:
        return [dbt_executable, command, "--profiles-dir", "."]
    return [sys.executable, "-m", "dbt.cli.main", command, "--profiles-dir", "."]


def _run_command(command: list[str], cwd: Path = PROJECT_ROOT) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def query_duckdb(sql: str) -> pd.DataFrame:
    ensure_data_artifacts()
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
    ensure_data_artifacts()
    return pd.read_parquet(GOLD_DIR / "ml_category_scores.parquet").sort_values(
        ["opportunity_rank", "category_id"]
    )


def load_public_query_metrics() -> pd.DataFrame:
    ensure_data_artifacts()
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
    ensure_data_artifacts()
    return json.loads((GOLD_DIR / "ml_model_metadata.json").read_text(encoding="utf-8"))


def load_advanced_ml_metadata() -> dict[str, Any]:
    ensure_data_artifacts()
    return json.loads((GOLD_DIR / "ml_advanced_metadata.json").read_text(encoding="utf-8"))

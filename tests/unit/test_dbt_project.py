from pathlib import Path


def test_dbt_project_contains_expected_layers():
    dbt_root = Path("dbt")

    assert (dbt_root / "dbt_project.yml").exists()
    assert (dbt_root / "profiles.yml").exists()
    assert (dbt_root / "models" / "staging" / "stg_categories.sql").exists()
    assert (dbt_root / "models" / "intermediate" / "int_category_snapshot_enriched.sql").exists()
    assert (dbt_root / "models" / "marts" / "mart_category_metrics.sql").exists()


def test_dbt_models_use_sources_and_refs():
    mart_sql = Path("dbt/models/marts/mart_category_metrics.sql").read_text(encoding="utf-8")
    staging_sql = Path("dbt/models/staging/stg_categories.sql").read_text(encoding="utf-8")

    assert "{{ ref('int_category_snapshot_enriched') }}" in mart_sql
    assert "{{ source('analytics', 'dim_category') }}" in staging_sql


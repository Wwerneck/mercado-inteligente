import json
from pathlib import Path

from src.config.settings import get_settings
from src.orchestration.pipeline_tasks import (
    build_observability_summary,
    extract_authenticated_marketplace_data,
    extract_marketplace_data,
    write_manifest,
    write_observability_summary,
)


def test_write_manifest_creates_observability_artifact(tmp_path: Path):
    path = write_manifest(
        tmp_path,
        "manual:2026-09-10",
        {"run_id": "manual:2026-09-10", "status": "success"},
    )

    payload = json.loads(path.read_text(encoding="utf-8"))

    assert path.exists()
    assert payload["status"] == "success"
    assert ":" not in path.name


def test_build_observability_summary_counts_rows_by_entity():
    summary = build_observability_summary(
        {
            "run_id": "run-1",
            "status": "success",
            "tasks": {
                "extract_marketplace_data": [
                    {"entity": "categories", "rows": 2},
                    {"entity": "domain_discovery", "rows": 3},
                ],
                "extract_authenticated_marketplace_data": {
                    "status": "success",
                    "outputs": [{"entity": "item_details", "rows": 4}],
                },
            },
        }
    )

    assert summary["task_count"] == 2
    assert summary["row_counts"] == {
        "categories": 2,
        "domain_discovery": 3,
        "item_details": 4,
    }
    assert summary["total_rows_processed"] == 9


def test_write_observability_summary_creates_gold_artifact(tmp_path: Path):
    path = write_observability_summary(
        tmp_path,
        {"run_id": "run-1", "status": "success", "tasks": {}},
    )

    payload = json.loads(path.read_text(encoding="utf-8"))

    assert path == tmp_path / "gold" / "pipeline_observability.json"
    assert payload["run_id"] == "run-1"


def test_extract_marketplace_data_uses_configured_public_queries(monkeypatch):
    captured: dict[str, list[str]] = {}
    monkeypatch.setenv("MELI_PUBLIC_QUERIES", "notebook,celular,geladeira")
    get_settings.cache_clear()

    def fake_run_batch_collection(queries: list[str]) -> list[dict[str, object]]:
        captured["queries"] = queries
        return []

    monkeypatch.setattr(
        "src.orchestration.pipeline_tasks.run_batch_collection",
        fake_run_batch_collection,
    )

    extract_marketplace_data()

    assert captured["queries"] == ["notebook", "celular", "geladeira"]


def test_extract_authenticated_marketplace_data_skips_without_token(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("MELI_ENABLE_AUTHENTICATED_COLLECTION", "true")
    monkeypatch.setenv("MELI_TOKEN_STORE_PATH", str(tmp_path / "missing_token.json"))
    get_settings.cache_clear()

    result = extract_authenticated_marketplace_data()

    assert result["status"] == "skipped"
    assert result["outputs"] == []


def test_extract_authenticated_marketplace_data_skips_when_disabled(monkeypatch):
    monkeypatch.setenv("MELI_ENABLE_AUTHENTICATED_COLLECTION", "false")
    get_settings.cache_clear()

    result = extract_authenticated_marketplace_data()

    assert result["status"] == "skipped"
    assert result["reason"] == "MELI_ENABLE_AUTHENTICATED_COLLECTION is false"


def test_extract_authenticated_marketplace_data_runs_when_token_exists(
    monkeypatch,
    tmp_path: Path,
):
    token_path = tmp_path / "token.json"
    token_path.write_text('{"access_token": "APP_USR-token"}', encoding="utf-8")
    monkeypatch.setenv("MELI_ENABLE_AUTHENTICATED_COLLECTION", "true")
    monkeypatch.setenv("MELI_TOKEN_STORE_PATH", str(token_path))
    get_settings.cache_clear()
    monkeypatch.setattr(
        "src.orchestration.pipeline_tasks.run_authenticated_collection",
        lambda: [{"entity": "authenticated_user", "rows": 1}],
    )

    result = extract_authenticated_marketplace_data()

    assert result["status"] == "success"
    assert result["outputs"][0]["entity"] == "authenticated_user"

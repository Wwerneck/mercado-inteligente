from pathlib import Path

import yaml

from src.config.settings import Settings


def test_docker_compose_has_required_services():
    compose = yaml.safe_load(Path("docker-compose.yml").read_text(encoding="utf-8"))

    assert {"postgres", "airflow-webserver", "airflow-scheduler", "fastapi", "streamlit"}.issubset(
        compose["services"]
    )


def test_ci_workflow_exists():
    assert Path(".github/workflows/ci.yml").exists()


def test_settings_parse_public_queries_from_csv():
    settings = Settings(MELI_PUBLIC_QUERIES="notebook, celular, smart tv")

    assert settings.public_queries == ["notebook", "celular", "smart tv"]

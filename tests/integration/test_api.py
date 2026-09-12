from fastapi.testclient import TestClient

from src.api.main import create_app


def test_health_endpoint():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_category_metrics_endpoint_returns_real_rows():
    client = TestClient(create_app())

    response = client.get("/analytics/categories")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 2
    assert "category_id" in payload["items"][0]


def test_overview_endpoint_returns_marketplace_kpis():
    client = TestClient(create_app())

    response = client.get("/analytics/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["total_categories"] >= 2
    assert payload[0]["latest_ingestion_at"] is not None


def test_category_detail_returns_404_for_unknown_category():
    client = TestClient(create_app())

    response = client.get("/analytics/categories/UNKNOWN")

    assert response.status_code == 404


def test_seller_item_metrics_endpoint_returns_paginated_response():
    client = TestClient(create_app())

    response = client.get("/analytics/seller-items")

    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert payload["limit"] == 50
    assert payload["offset"] == 0
    assert "total" in payload


def test_seller_items_endpoint_returns_paginated_response():
    client = TestClient(create_app())

    response = client.get("/analytics/items")

    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert payload["limit"] == 50
    assert payload["offset"] == 0
    assert "total" in payload


def test_pipeline_runs_endpoint_returns_paginated_response():
    client = TestClient(create_app())

    response = client.get("/pipeline/runs")

    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert payload["limit"] == 20
    assert "total" in payload


def test_latest_pipeline_run_endpoint_returns_manifest():
    client = TestClient(create_app())

    response = client.get("/pipeline/runs/latest")

    assert response.status_code == 200
    assert "run_id" in response.json()


def test_ml_opportunity_endpoint_returns_scores():
    client = TestClient(create_app())

    response = client.get("/ml/opportunity-score")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 2
    assert "opportunity_score" in payload["items"][0]


def test_ai_ask_endpoint_returns_controlled_answer():
    client = TestClient(create_app())

    response = client.post(
        "/ai/ask",
        json={"question": "Quais categorias possuem maior Opportunity Score?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "top_opportunities"
    assert payload["sources"]

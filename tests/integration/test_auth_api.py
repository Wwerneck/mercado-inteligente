from fastapi.testclient import TestClient

from src.api.main import create_app
from src.config.settings import get_settings


def test_meli_authorize_requires_oauth_settings(monkeypatch):
    monkeypatch.setenv("MELI_CLIENT_ID", "")
    monkeypatch.setenv("MELI_CLIENT_SECRET", "")
    monkeypatch.setenv("MELI_REDIRECT_URI", "")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/auth/meli/authorize")

    assert response.status_code == 503
    assert "MELI_CLIENT_ID" in response.json()["detail"]


def test_meli_authorize_returns_url_with_pkce(monkeypatch):
    monkeypatch.setenv("MELI_CLIENT_ID", "123")
    monkeypatch.setenv("MELI_CLIENT_SECRET", "secret")
    monkeypatch.setenv("MELI_REDIRECT_URI", "http://localhost:8000/auth/meli/callback")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/auth/meli/authorize?use_pkce=true")

    assert response.status_code == 200
    payload = response.json()
    assert "https://auth.mercadolivre.com.br/authorization" in payload["authorization_url"]
    assert "state=" in payload["authorization_url"]
    assert payload["state"]
    assert payload["code_verifier"]
    assert payload["code_challenge_method"] == "S256"


def test_meli_callback_rejects_mismatched_state(monkeypatch):
    monkeypatch.setenv("MELI_CLIENT_ID", "123")
    monkeypatch.setenv("MELI_CLIENT_SECRET", "secret")
    monkeypatch.setenv("MELI_REDIRECT_URI", "http://localhost:8000/auth/meli/callback")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.post(
        "/auth/meli/callback",
        json={"code": "abc", "state": "actual", "expected_state": "expected"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "OAuth state invalido"


def test_meli_browser_callback_exchanges_code_and_stores_token(monkeypatch, tmp_path):
    token_path = tmp_path / "meli_token.json"
    monkeypatch.setenv("MELI_CLIENT_ID", "123")
    monkeypatch.setenv("MELI_CLIENT_SECRET", "secret")
    monkeypatch.setenv("MELI_REDIRECT_URI", "http://localhost:8000/auth/meli/callback")
    monkeypatch.setenv("MELI_TOKEN_STORE_PATH", str(token_path))
    get_settings.cache_clear()

    def fake_exchange_code(self, client_id, client_secret, code, redirect_uri, code_verifier=None):
        assert client_id == "123"
        assert client_secret == "secret"
        assert code == "abc"
        assert redirect_uri == "http://localhost:8000/auth/meli/callback"
        return {"access_token": "APP_USR-abcdef1234567890", "user_id": 123}

    monkeypatch.setattr(
        "src.api.routers.auth.MercadoLivreOAuthClient.exchange_code",
        fake_exchange_code,
    )
    client = TestClient(create_app())

    response = client.get("/auth/meli/callback?code=abc&state=returned")

    assert response.status_code == 200
    assert response.json()["access_token"] == "APP_USR-abcdef1234567890"
    assert token_path.exists()


def test_meli_status_masks_stored_token(monkeypatch, tmp_path):
    token_path = tmp_path / "meli_token.json"
    token_path.write_text(
        """{
  "access_token": "APP_USR-abcdef1234567890",
  "token_type": "bearer",
  "refresh_token": "TG-refresh1234567890",
  "user_id": 123,
  "scope": "offline_access read",
  "expires_at": null,
  "saved_at": "2026-09-11T10:00:00+00:00"
}""",
        encoding="utf-8",
    )
    monkeypatch.setenv("MELI_CLIENT_ID", "123")
    monkeypatch.setenv("MELI_CLIENT_SECRET", "secret")
    monkeypatch.setenv("MELI_TOKEN_STORE_PATH", str(token_path))
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/auth/meli/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["configured"] is True
    assert payload["token"]["access_token"] == "APP_US...7890"
    assert payload["token"]["refresh_token"] == "TG-ref...7890"

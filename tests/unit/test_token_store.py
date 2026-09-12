import json

import pytest

from src.ingestion.token_store import (
    generate_token_encryption_key,
    load_meli_token,
    save_meli_token,
)


def test_save_and_load_meli_token_masks_secrets(tmp_path):
    path = tmp_path / "token.json"

    token = save_meli_token(
        {
            "access_token": "APP_USR-abcdef1234567890",
            "token_type": "bearer",
            "expires_in": 3600,
            "scope": "offline_access read",
            "user_id": 123,
            "refresh_token": "TG-refresh1234567890",
        },
        path,
    )

    loaded = load_meli_token(path)

    assert token.access_token == "APP_USR-abcdef1234567890"
    assert loaded is not None
    assert loaded.user_id == 123
    assert loaded.expires_at is not None
    assert loaded.masked()["access_token"] == "APP_US...7890"
    assert loaded.masked()["refresh_token"] == "TG-ref...7890"


def test_save_and_load_meli_token_with_encryption_key(tmp_path):
    path = tmp_path / "token.json"
    encryption_key = generate_token_encryption_key()

    save_meli_token(
        {
            "access_token": "APP_USR-secret-token",
            "refresh_token": "TG-refresh-secret",
        },
        path,
        encryption_key,
    )

    raw_payload = json.loads(path.read_text(encoding="utf-8"))
    loaded = load_meli_token(path, encryption_key)

    assert raw_payload["encrypted"] is True
    assert "APP_USR-secret-token" not in path.read_text(encoding="utf-8")
    assert loaded is not None
    assert loaded.access_token == "APP_USR-secret-token"
    assert loaded.refresh_token == "TG-refresh-secret"


def test_load_encrypted_meli_token_requires_key(tmp_path):
    path = tmp_path / "token.json"
    save_meli_token(
        {"access_token": "APP_USR-secret-token"},
        path,
        generate_token_encryption_key(),
    )

    with pytest.raises(ValueError, match="MELI_TOKEN_ENCRYPTION_KEY"):
        load_meli_token(path)

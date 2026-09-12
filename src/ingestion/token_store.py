from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

TOKEN_STORE_VERSION = 1


@dataclass(frozen=True)
class StoredMeliToken:
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None
    scope: str | None = None
    user_id: int | None = None
    expires_at: str | None = None
    saved_at: str | None = None

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.fromisoformat(self.expires_at) <= datetime.now(UTC)

    def masked(self) -> dict[str, Any]:
        return {
            "access_token": _mask(self.access_token),
            "token_type": self.token_type,
            "refresh_token": _mask(self.refresh_token),
            "scope": self.scope,
            "user_id": self.user_id,
            "expires_at": self.expires_at,
            "saved_at": self.saved_at,
            "is_expired": self.is_expired,
        }


def save_meli_token(
    payload: dict[str, Any], path: Path, encryption_key: str | None = None
) -> StoredMeliToken:
    token = _token_from_oauth_payload(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(token.__dict__, indent=2, sort_keys=True)
    if encryption_key:
        encrypted_payload = {
            "version": TOKEN_STORE_VERSION,
            "encrypted": True,
            "payload": _fernet(encryption_key).encrypt(serialized.encode("utf-8")).decode("utf-8"),
        }
        path.write_text(json.dumps(encrypted_payload, indent=2, sort_keys=True), encoding="utf-8")
    else:
        path.write_text(serialized, encoding="utf-8")
    return token


def load_meli_token(path: Path, encryption_key: str | None = None) -> StoredMeliToken | None:
    if not path.exists():
        return None
    stored_payload = json.loads(path.read_text(encoding="utf-8"))
    payload = _decrypt_payload(stored_payload, encryption_key)
    return StoredMeliToken(
        access_token=payload["access_token"],
        token_type=payload.get("token_type", "bearer"),
        refresh_token=payload.get("refresh_token"),
        scope=payload.get("scope"),
        user_id=payload.get("user_id"),
        expires_at=payload.get("expires_at"),
        saved_at=payload.get("saved_at"),
    )


def _token_from_oauth_payload(payload: dict[str, Any]) -> StoredMeliToken:
    now = datetime.now(UTC)
    expires_in = payload.get("expires_in")
    expires_at = None
    if isinstance(expires_in, int):
        expires_at = (now + timedelta(seconds=expires_in)).isoformat()

    return StoredMeliToken(
        access_token=payload["access_token"],
        token_type=payload.get("token_type", "bearer"),
        refresh_token=payload.get("refresh_token"),
        scope=payload.get("scope"),
        user_id=payload.get("user_id"),
        expires_at=expires_at,
        saved_at=now.isoformat(),
    )


def _mask(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 10:
        return "***"
    return f"{value[:6]}...{value[-4:]}"


def generate_token_encryption_key() -> str:
    return Fernet.generate_key().decode("utf-8")


def _decrypt_payload(payload: dict[str, Any], encryption_key: str | None) -> dict[str, Any]:
    if not payload.get("encrypted"):
        return payload
    if not encryption_key:
        raise ValueError("Token OAuth criptografado exige MELI_TOKEN_ENCRYPTION_KEY")
    try:
        decrypted = _fernet(encryption_key).decrypt(payload["payload"].encode("utf-8"))
    except InvalidToken as exc:
        raise ValueError("MELI_TOKEN_ENCRYPTION_KEY invalida para o token OAuth") from exc
    return json.loads(decrypted.decode("utf-8"))


def _fernet(encryption_key: str) -> Fernet:
    return Fernet(encryption_key.encode("utf-8"))

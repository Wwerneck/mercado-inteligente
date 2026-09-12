from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx


class MercadoLivreOAuthError(RuntimeError):
    pass


@dataclass(frozen=True)
class PKCEPair:
    verifier: str
    challenge: str
    method: str = "S256"


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def generate_pkce_pair() -> PKCEPair:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return PKCEPair(verifier=verifier, challenge=challenge)


def build_authorization_url(
    auth_base_url: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    pkce_pair: PKCEPair | None = None,
) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    if pkce_pair:
        params["code_challenge"] = pkce_pair.challenge
        params["code_challenge_method"] = pkce_pair.method
    return f"{auth_base_url.rstrip('/')}/authorization?{urlencode(params)}"


class MercadoLivreOAuthClient:
    def __init__(self, base_url: str, timeout_seconds: float = 20.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def exchange_code(
        self,
        client_id: str,
        client_secret: str,
        code: str,
        redirect_uri: str,
        code_verifier: str | None = None,
    ) -> dict[str, Any]:
        data = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        }
        if code_verifier:
            data["code_verifier"] = code_verifier
        return self._post_token(data)

    def refresh_token(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ) -> dict[str, Any]:
        return self._post_token(
            {
                "grant_type": "refresh_token",
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
            }
        )

    def _post_token(self, data: dict[str, str]) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{self.base_url}/oauth/token",
                data=data,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            details = exc.response.text[:500] if exc.response is not None else str(exc)
            raise MercadoLivreOAuthError(
                f"Mercado Livre OAuth request failed: {details}"
            ) from exc
        except httpx.HTTPError as exc:
            raise MercadoLivreOAuthError("Mercado Livre OAuth request failed") from exc

        if not isinstance(payload, dict) or "access_token" not in payload:
            raise MercadoLivreOAuthError("Mercado Livre OAuth response did not include access_token")
        return payload

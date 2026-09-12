from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.api.schemas import (
    MeliAuthorizationResponse,
    MeliOAuthCallbackRequest,
    MeliRefreshTokenRequest,
    MeliTokenResponse,
    MeliTokenStatusResponse,
)
from src.config.settings import get_settings
from src.ingestion.oauth import (
    MercadoLivreOAuthClient,
    MercadoLivreOAuthError,
    build_authorization_url,
    generate_pkce_pair,
    generate_state,
)
from src.ingestion.token_store import load_meli_token, save_meli_token

router = APIRouter(prefix="/auth/meli", tags=["auth"])


def _require_oauth_settings() -> tuple[str, str, str]:
    settings = get_settings()
    missing = [
        name
        for name, value in {
            "MELI_CLIENT_ID": settings.meli_client_id,
            "MELI_CLIENT_SECRET": settings.meli_client_secret,
            "MELI_REDIRECT_URI": settings.meli_redirect_uri,
        }.items()
        if not value
    ]
    if missing:
        raise HTTPException(
            status_code=503,
            detail=f"OAuth Mercado Livre nao configurado: {', '.join(missing)}",
        )
    return settings.meli_client_id, settings.meli_client_secret, settings.meli_redirect_uri


def _token_response(payload: dict[str, Any]) -> MeliTokenResponse:
    return MeliTokenResponse(
        access_token=payload["access_token"],
        token_type=payload.get("token_type", "bearer"),
        expires_in=payload.get("expires_in"),
        scope=payload.get("scope"),
        user_id=payload.get("user_id"),
        refresh_token=payload.get("refresh_token"),
    )


@router.get("/authorize", response_model=MeliAuthorizationResponse)
def authorize(use_pkce: bool | None = Query(default=None)) -> MeliAuthorizationResponse:
    client_id, _, redirect_uri = _require_oauth_settings()
    settings = get_settings()
    state = generate_state()
    should_use_pkce = settings.meli_use_pkce if use_pkce is None else use_pkce
    pkce_pair = generate_pkce_pair() if should_use_pkce else None

    authorization_url = build_authorization_url(
        auth_base_url=settings.meli_auth_base_url,
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=state,
        pkce_pair=pkce_pair,
    )
    return MeliAuthorizationResponse(
        authorization_url=authorization_url,
        state=state,
        code_verifier=pkce_pair.verifier if pkce_pair else None,
        code_challenge_method=pkce_pair.method if pkce_pair else None,
    )


@router.post("/callback", response_model=MeliTokenResponse)
def callback(payload: MeliOAuthCallbackRequest) -> MeliTokenResponse:
    client_id, client_secret, redirect_uri = _require_oauth_settings()
    if payload.expected_state and payload.state != payload.expected_state:
        raise HTTPException(status_code=400, detail="OAuth state invalido")

    client = MercadoLivreOAuthClient(get_settings().meli_base_url)
    token_payload = client.exchange_code(
        client_id=client_id,
        client_secret=client_secret,
        code=payload.code,
        redirect_uri=redirect_uri,
        code_verifier=payload.code_verifier,
    )
    settings = get_settings()
    save_meli_token(
        token_payload,
        settings.meli_token_store_path,
        settings.meli_token_encryption_key,
    )
    return _token_response(token_payload)


@router.get("/callback", response_model=MeliTokenResponse)
def browser_callback(
    code: str = Query(min_length=1),
    state: str | None = Query(default=None),
    code_verifier: str | None = Query(default=None),
) -> MeliTokenResponse:
    client_id, client_secret, redirect_uri = _require_oauth_settings()
    client = MercadoLivreOAuthClient(get_settings().meli_base_url)
    try:
        token_payload = client.exchange_code(
            client_id=client_id,
            client_secret=client_secret,
            code=code,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier,
        )
    except MercadoLivreOAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    settings = get_settings()
    save_meli_token(
        token_payload,
        settings.meli_token_store_path,
        settings.meli_token_encryption_key,
    )
    return _token_response(token_payload)


@router.post("/refresh", response_model=MeliTokenResponse)
def refresh(payload: MeliRefreshTokenRequest) -> MeliTokenResponse:
    client_id, client_secret, _ = _require_oauth_settings()
    client = MercadoLivreOAuthClient(get_settings().meli_base_url)
    token_payload = client.refresh_token(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=payload.refresh_token,
    )
    settings = get_settings()
    save_meli_token(
        token_payload,
        settings.meli_token_store_path,
        settings.meli_token_encryption_key,
    )
    return _token_response(token_payload)


@router.get("/status", response_model=MeliTokenStatusResponse)
def status() -> MeliTokenStatusResponse:
    settings = get_settings()
    token = load_meli_token(settings.meli_token_store_path, settings.meli_token_encryption_key)
    return MeliTokenStatusResponse(
        configured=bool(settings.meli_client_id and settings.meli_client_secret),
        token_path=str(settings.meli_token_store_path),
        token=token.masked() if token else None,
    )

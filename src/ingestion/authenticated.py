from __future__ import annotations

from typing import Any

from src.config.settings import Settings
from src.ingestion.api_client import MercadoLivreAPIError, MercadoLivreClient
from src.ingestion.oauth import MercadoLivreOAuthClient
from src.ingestion.token_store import StoredMeliToken, load_meli_token, save_meli_token


class MercadoLivreAuthenticationError(RuntimeError):
    pass


def load_valid_meli_token(settings: Settings) -> StoredMeliToken:
    token = load_meli_token(
        settings.meli_token_store_path, settings.meli_token_encryption_key
    )
    if token is None:
        raise MercadoLivreAuthenticationError(
            f"Token OAuth nao encontrado em {settings.meli_token_store_path}"
        )
    if not token.is_expired:
        return token
    if not token.refresh_token:
        raise MercadoLivreAuthenticationError("Token OAuth expirado e sem refresh_token")
    if not settings.meli_client_id or not settings.meli_client_secret:
        raise MercadoLivreAuthenticationError(
            "MELI_CLIENT_ID e MELI_CLIENT_SECRET sao necessarios para renovar token"
        )

    oauth_client = MercadoLivreOAuthClient(settings.meli_base_url, settings.meli_timeout_seconds)
    refreshed_payload = oauth_client.refresh_token(
        client_id=settings.meli_client_id,
        client_secret=settings.meli_client_secret,
        refresh_token=token.refresh_token,
    )
    return save_meli_token(
        refreshed_payload,
        settings.meli_token_store_path,
        settings.meli_token_encryption_key,
    )


def fetch_authenticated_user(client: MercadoLivreClient, token: StoredMeliToken) -> dict[str, Any]:
    payload = client.get_authenticated("/users/me", access_token=token.access_token)
    if not isinstance(payload, dict):
        raise MercadoLivreAPIError("/users/me payload is not a JSON object")
    return payload


def fetch_seller_item_ids(
    client: MercadoLivreClient,
    token: StoredMeliToken,
    user_id: int | str,
    limit: int = 100,
    max_pages: int = 10,
    status: str | None = None,
) -> list[dict[str, Any]]:
    normalized_limit = max(1, min(limit, 100))
    items: list[dict[str, Any]] = []

    for page in range(max_pages):
        params: dict[str, Any] = {"limit": normalized_limit, "offset": page * normalized_limit}
        if status:
            params["status"] = status

        payload = client.get_authenticated(
            f"/users/{user_id}/items/search",
            access_token=token.access_token,
            params=params,
        )
        if not isinstance(payload, dict):
            raise MercadoLivreAPIError("Seller items payload is not a JSON object")

        results = payload.get("results", [])
        if not isinstance(results, list):
            raise MercadoLivreAPIError("Seller items payload does not contain a results list")

        items.extend(
            {"id": item_id, "seller_id": str(user_id)}
            for item_id in results
            if isinstance(item_id, str)
        )

        paging = payload.get("paging", {})
        total = int(paging.get("total", 0)) if isinstance(paging, dict) else 0
        if not results or (page + 1) * normalized_limit >= total:
            break

    return items


def fetch_item_details(
    client: MercadoLivreClient,
    token: StoredMeliToken,
    item_ids: list[str],
    batch_size: int = 20,
    attributes: list[str] | None = None,
) -> list[dict[str, Any]]:
    unique_item_ids = [item_id for item_id in dict.fromkeys(item_ids) if item_id]
    details: list[dict[str, Any]] = []

    for start in range(0, len(unique_item_ids), batch_size):
        batch = unique_item_ids[start : start + batch_size]
        params: dict[str, Any] = {"ids": ",".join(batch)}
        if attributes:
            params["attributes"] = ",".join(attributes)

        payload = client.get_authenticated(
            "/items",
            access_token=token.access_token,
            params=params,
        )
        if not isinstance(payload, list):
            raise MercadoLivreAPIError("Items multiget payload is not a JSON list")

        for item in payload:
            if not isinstance(item, dict):
                continue
            body = item.get("body")
            status_code = item.get("code")
            if isinstance(status_code, int) and 200 <= status_code < 300 and isinstance(body, dict):
                details.append(body)

    return details


def fetch_item_descriptions(
    client: MercadoLivreClient,
    token: StoredMeliToken,
    item_ids: list[str],
) -> list[dict[str, Any]]:
    descriptions: list[dict[str, Any]] = []
    for item_id in [item_id for item_id in dict.fromkeys(item_ids) if item_id]:
        try:
            payload = client.get_authenticated(
                f"/items/{item_id}/description",
                access_token=token.access_token,
            )
        except MercadoLivreAPIError:
            continue
        if isinstance(payload, dict):
            descriptions.append({"id": item_id, **payload})
    return descriptions


def build_item_price_snapshots(
    item_details: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = []
    for item in item_details:
        item_id = item.get("id")
        if not item_id:
            continue
        snapshots.append(
            {
                "id": item_id,
                "item_id": item_id,
                "seller_id": item.get("seller_id"),
                "category_id": item.get("category_id"),
                "price": item.get("price"),
                "base_price": item.get("base_price"),
                "original_price": item.get("original_price"),
                "currency_id": item.get("currency_id"),
                "available_quantity": item.get("available_quantity"),
                "sold_quantity": item.get("sold_quantity"),
                "status": item.get("status"),
                "condition": item.get("condition"),
                "last_updated": item.get("last_updated"),
            }
        )
    return snapshots

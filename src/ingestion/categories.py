from typing import Any

from src.ingestion.api_client import MercadoLivreClient


def fetch_site_categories(client: MercadoLivreClient, site_id: str) -> list[dict[str, Any]]:
    payload = client.get(f"/sites/{site_id}/categories")
    if isinstance(payload, list):
        return [category for category in payload if isinstance(category, dict)]
    categories = payload.get("categories", [])
    if not isinstance(categories, list):
        raise TypeError("Categories payload does not contain a categories list")
    return [category for category in categories if isinstance(category, dict)]


def fetch_categories_by_id(client: MercadoLivreClient, category_ids: list[str]) -> list[dict[str, Any]]:
    categories: list[dict[str, Any]] = []
    for category_id in dict.fromkeys(category_ids):
        payload = client.get(f"/categories/{category_id}")
        if isinstance(payload, dict):
            categories.append(payload)
    return categories

from typing import Any

from src.ingestion.api_client import MercadoLivreClient


def search_products(
    client: MercadoLivreClient,
    site_id: str,
    query: str,
    limit: int = 50,
    max_pages: int = 1,
) -> list[dict[str, Any]]:
    return list(client.paginate_search(query=query, site_id=site_id, limit=limit, max_pages=max_pages))


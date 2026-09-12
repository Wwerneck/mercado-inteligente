from typing import Any

from src.ingestion.api_client import MercadoLivreClient


def discover_domains(client: MercadoLivreClient, site_id: str, query: str) -> list[dict[str, Any]]:
    payload = client.get(f"/sites/{site_id}/domain_discovery/search", params={"q": query})
    if not isinstance(payload, list):
        raise TypeError("Domain discovery payload is not a list")
    return [domain for domain in payload if isinstance(domain, dict)]

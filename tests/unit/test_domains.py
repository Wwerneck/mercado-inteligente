import httpx

from src.ingestion.api_client import MercadoLivreClient
from src.ingestion.domains import discover_domains


def test_discover_domains_returns_list_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                {
                    "domain_id": "MLB-NOTEBOOKS",
                    "domain_name": "Notebooks",
                    "category_id": "MLB1652",
                    "category_name": "Notebooks",
                }
            ],
        )

    client = MercadoLivreClient("https://api.test", rate_limit_seconds=0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.test")

    domains = discover_domains(client, "MLB", "notebook")

    assert domains[0]["category_id"] == "MLB1652"
    client.close()

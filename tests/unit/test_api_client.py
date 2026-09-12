import httpx

from src.ingestion.api_client import MercadoLivreClient


def test_get_returns_dict_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    client = MercadoLivreClient("https://api.test", rate_limit_seconds=0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.test")

    assert client.get("/health") == {"ok": True}
    client.close()


def test_paginate_search_yields_results():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "paging": {"total": 1},
                "results": [{"id": "MLB1", "title": "Produto"}],
            },
        )

    client = MercadoLivreClient("https://api.test", rate_limit_seconds=0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.test")

    results = list(client.paginate_search("notebook", "MLB"))

    assert results == [{"id": "MLB1", "title": "Produto"}]
    client.close()


def test_get_authenticated_sends_bearer_token():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer APP_USR-token"
        return httpx.Response(200, json={"id": 123})

    client = MercadoLivreClient("https://api.test", rate_limit_seconds=0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.test")

    assert client.get_authenticated("/users/me", access_token="APP_USR-token") == {"id": 123}
    client.close()

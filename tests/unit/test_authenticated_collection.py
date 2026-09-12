import httpx

from src.config.settings import get_settings
from src.ingestion.api_client import MercadoLivreClient
from src.ingestion.authenticated import (
    build_item_price_snapshots,
    fetch_authenticated_user,
    fetch_item_descriptions,
    fetch_item_details,
    fetch_seller_item_ids,
    load_valid_meli_token,
)
from src.ingestion.run_authenticated_collection import run_authenticated_collection
from src.ingestion.token_store import save_meli_token


def test_fetch_authenticated_user_calls_users_me(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/users/me"
        assert request.headers["Authorization"] == "Bearer APP_USR-token"
        return httpx.Response(200, json={"id": 123, "nickname": "seller"})

    client = MercadoLivreClient("https://api.test", rate_limit_seconds=0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.test")

    token = save_meli_token({"access_token": "APP_USR-token"}, tmp_path / "token.json")

    payload = fetch_authenticated_user(client, token=token)

    assert payload == {"id": 123, "nickname": "seller"}
    client.close()


def test_load_valid_meli_token_returns_stored_active_token(monkeypatch, tmp_path):
    token_path = tmp_path / "token.json"
    save_meli_token({"access_token": "APP_USR-token", "expires_in": 3600}, token_path)
    monkeypatch.setenv("MELI_TOKEN_STORE_PATH", str(token_path))
    get_settings.cache_clear()

    token = load_valid_meli_token(get_settings())

    assert token.access_token == "APP_USR-token"


def test_fetch_seller_item_ids_paginates_until_total(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/users/123/items/search"
        assert request.headers["Authorization"] == "Bearer APP_USR-token"
        offset = int(request.url.params["offset"])
        if offset == 0:
            return httpx.Response(
                200,
                json={"results": ["MLB1", "MLB2"], "paging": {"total": 3}},
            )
        return httpx.Response(
            200,
            json={"results": ["MLB3"], "paging": {"total": 3}},
        )

    client = MercadoLivreClient("https://api.test", rate_limit_seconds=0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.test")
    token = save_meli_token({"access_token": "APP_USR-token"}, tmp_path / "token.json")

    items = fetch_seller_item_ids(client, token=token, user_id=123, limit=2)

    assert items == [
        {"id": "MLB1", "seller_id": "123"},
        {"id": "MLB2", "seller_id": "123"},
        {"id": "MLB3", "seller_id": "123"},
    ]
    client.close()


def test_fetch_item_details_uses_multiget_and_keeps_successful_bodies(tmp_path):
    seen_ids: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/items"
        assert request.headers["Authorization"] == "Bearer APP_USR-token"
        seen_ids.extend(request.url.params["ids"].split(","))
        return httpx.Response(
            200,
            json=[
                {"code": 200, "body": {"id": "MLB1", "price": 10}},
                {"code": 404, "body": {"id": "MLB404"}},
            ],
        )

    client = MercadoLivreClient("https://api.test", rate_limit_seconds=0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.test")
    token = save_meli_token({"access_token": "APP_USR-token"}, tmp_path / "token.json")

    details = fetch_item_details(client, token=token, item_ids=["MLB1", "MLB1"], batch_size=1)

    assert seen_ids == ["MLB1"]
    assert details == [{"id": "MLB1", "price": 10}]
    client.close()


def test_fetch_item_descriptions_keeps_successful_payloads(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/items/MLB1/description"
        assert request.headers["Authorization"] == "Bearer APP_USR-token"
        return httpx.Response(200, json={"plain_text": "Descricao do produto"})

    client = MercadoLivreClient("https://api.test", rate_limit_seconds=0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.test")
    token = save_meli_token({"access_token": "APP_USR-token"}, tmp_path / "token.json")

    descriptions = fetch_item_descriptions(client, token=token, item_ids=["MLB1", "MLB1"])

    assert descriptions == [{"id": "MLB1", "plain_text": "Descricao do produto"}]
    client.close()


def test_build_item_price_snapshots_extracts_temporal_fields():
    snapshots = build_item_price_snapshots(
        [
            {
                "id": "MLB1",
                "seller_id": 123,
                "category_id": "MLB1652",
                "price": 100,
                "available_quantity": 5,
                "sold_quantity": 2,
                "status": "active",
            }
        ]
    )

    assert snapshots == [
        {
            "id": "MLB1",
            "item_id": "MLB1",
            "seller_id": 123,
            "category_id": "MLB1652",
            "price": 100,
            "base_price": None,
            "original_price": None,
            "currency_id": None,
            "available_quantity": 5,
            "sold_quantity": 2,
            "status": "active",
            "condition": None,
            "last_updated": None,
        }
    ]


def test_run_authenticated_collection_writes_user_and_items(monkeypatch, tmp_path):
    token_path = tmp_path / "token.json"
    save_meli_token({"access_token": "APP_USR-token", "expires_in": 3600}, token_path)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MELI_TOKEN_STORE_PATH", str(token_path))
    get_settings.cache_clear()

    monkeypatch.setattr(
        "src.ingestion.run_authenticated_collection.fetch_authenticated_user",
        lambda client, token: {"id": 123, "nickname": "seller"},
    )
    monkeypatch.setattr(
        "src.ingestion.run_authenticated_collection.fetch_seller_item_ids",
        lambda client, token, user_id: [{"id": "MLB1", "seller_id": str(user_id)}],
    )
    monkeypatch.setattr(
        "src.ingestion.run_authenticated_collection.fetch_item_details",
        lambda client, token, item_ids: [{"id": item_ids[0], "price": 10}],
    )
    monkeypatch.setattr(
        "src.ingestion.run_authenticated_collection.fetch_item_descriptions",
        lambda client, token, item_ids: [{"id": item_ids[0], "plain_text": "Descricao"}],
    )

    outputs = run_authenticated_collection()

    assert [output["entity"] for output in outputs] == [
        "authenticated_user",
        "seller_items",
        "item_details",
        "item_descriptions",
        "item_price_snapshots",
    ]
    assert outputs[0]["rows"] == 1
    assert outputs[1]["rows"] == 1
    assert outputs[2]["rows"] == 1
    assert outputs[3]["rows"] == 1
    assert outputs[4]["rows"] == 1

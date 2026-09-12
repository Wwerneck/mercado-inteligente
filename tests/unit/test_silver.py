import json

import pandas as pd

from src.processing.silver import (
    transform_categories,
    transform_domain_discovery,
    transform_item_descriptions,
    transform_item_details,
    transform_item_price_snapshots,
)


def test_transform_domain_discovery_deduplicates_by_domain_id():
    bronze = pd.DataFrame(
        [
            {
                "ingested_at": "2026-09-10T10:00:00+00:00",
                "source": "mercado_livre",
                "endpoint": "/sites/MLB/domain_discovery/search?q=notebook",
                "payload": json.dumps(
                    {
                        "domain_id": "MLB-NOTEBOOKS",
                        "domain_name": "Notebooks",
                        "category_id": "MLB1652",
                        "category_name": "Notebooks",
                    }
                ),
            }
        ]
    )

    silver = transform_domain_discovery(bronze)

    assert silver.loc[0, "domain_id"] == "MLB-NOTEBOOKS"
    assert silver.loc[0, "category_id"] == "MLB1652"
    assert silver.loc[0, "domain_category_id"] == "MLB-NOTEBOOKS__MLB1652"
    assert silver.loc[0, "query_domain_category_id"] == "notebook__MLB-NOTEBOOKS__MLB1652"


def test_transform_domain_discovery_preserves_query_grain():
    bronze = pd.DataFrame(
        [
            {
                "ingested_at": "2026-09-10T10:00:00+00:00",
                "source": "mercado_livre",
                "endpoint": "/sites/MLB/domain_discovery/search?q=notebook",
                "payload": json.dumps(
                    {
                        "domain_id": "MLB-NOTEBOOKS",
                        "domain_name": "Notebooks",
                        "category_id": "MLB1652",
                        "category_name": "Notebooks",
                    }
                ),
            },
            {
                "ingested_at": "2026-09-10T11:00:00+00:00",
                "source": "mercado_livre",
                "endpoint": "/sites/MLB/domain_discovery/search?q=computador",
                "payload": json.dumps(
                    {
                        "domain_id": "MLB-NOTEBOOKS",
                        "domain_name": "Notebooks",
                        "category_id": "MLB1652",
                        "category_name": "Notebooks",
                    }
                ),
            },
        ]
    )

    silver = transform_domain_discovery(bronze)

    assert len(silver) == 2
    assert sorted(silver["search_query"].tolist()) == ["computador", "notebook"]


def test_transform_categories_extracts_nested_fields():
    bronze = pd.DataFrame(
        [
            {
                "record_id": "MLB1652",
                "ingested_at": "2026-09-10T10:00:00+00:00",
                "source": "mercado_livre",
                "payload": json.dumps(
                    {
                        "id": "MLB1652",
                        "name": "Notebooks",
                        "picture": "https://example.com/image.png",
                        "total_items_in_this_category": 100,
                        "path_from_root": [{"id": "MLB1648", "name": "Computacao"}],
                        "children_categories": [{"id": "MLB1", "name": "A"}],
                        "settings": {"adult_content": False},
                    }
                ),
            }
        ]
    )

    silver = transform_categories(bronze)

    assert silver.loc[0, "category_id"] == "MLB1652"
    assert silver.loc[0, "children_categories_count"] == 1
    assert silver.loc[0, "path_from_root"] == "Computacao"


def test_transform_item_details_extracts_commercial_fields():
    bronze = pd.DataFrame(
        [
            {
                "record_id": "MLB1",
                "ingested_at": "2026-09-10T10:00:00+00:00",
                "source": "mercado_livre_oauth",
                "payload": json.dumps(
                    {
                        "id": "MLB1",
                        "title": "Notebook",
                        "price": 2500.5,
                        "currency_id": "BRL",
                        "available_quantity": 7,
                        "sold_quantity": 3,
                        "status": "active",
                        "condition": "new",
                        "category_id": "MLB1652",
                        "listing_type_id": "gold_special",
                        "permalink": "https://produto.mercadolivre.com.br/MLB1",
                        "seller_id": 123,
                        "site_id": "MLB",
                        "date_created": "2026-09-01T12:00:00.000Z",
                        "last_updated": "2026-09-10T12:00:00.000Z",
                    }
                ),
            }
        ]
    )

    silver = transform_item_details(bronze)

    assert silver.loc[0, "item_id"] == "MLB1"
    assert silver.loc[0, "price"] == 2500.5
    assert silver.loc[0, "seller_id"] == "123"
    assert str(silver.loc[0, "date_created"].tzinfo) == "UTC"


def test_transform_item_details_keeps_latest_record_per_item():
    bronze = pd.DataFrame(
        [
            {
                "record_id": "MLB1",
                "ingested_at": "2026-09-10T10:00:00+00:00",
                "source": "mercado_livre_oauth",
                "payload": json.dumps({"id": "MLB1", "title": "Old", "price": 100}),
            },
            {
                "record_id": "MLB1",
                "ingested_at": "2026-09-11T10:00:00+00:00",
                "source": "mercado_livre_oauth",
                "payload": json.dumps({"id": "MLB1", "title": "New", "price": 90}),
            },
        ]
    )

    silver = transform_item_details(bronze)

    assert len(silver) == 1
    assert silver.loc[0, "title"] == "New"
    assert silver.loc[0, "price"] == 90


def test_transform_item_price_snapshots_keeps_temporal_history():
    bronze = pd.DataFrame(
        [
            {
                "record_id": "MLB1",
                "ingested_at": "2026-09-10T10:00:00+00:00",
                "source": "mercado_livre_oauth",
                "payload": json.dumps(
                    {
                        "id": "MLB1",
                        "seller_id": 123,
                        "category_id": "MLB1652",
                        "price": 100,
                        "available_quantity": 5,
                        "sold_quantity": 2,
                        "status": "active",
                    }
                ),
            },
            {
                "record_id": "MLB1",
                "ingested_at": "2026-09-11T10:00:00+00:00",
                "source": "mercado_livre_oauth",
                "payload": json.dumps(
                    {
                        "id": "MLB1",
                        "seller_id": 123,
                        "category_id": "MLB1652",
                        "price": 90,
                        "available_quantity": 4,
                        "sold_quantity": 3,
                        "status": "active",
                    }
                ),
            },
        ]
    )

    silver = transform_item_price_snapshots(bronze)

    assert len(silver) == 2
    assert silver["price"].tolist() == [100, 90]
    assert silver["snapshot_date_key"].tolist() == [20260910, 20260911]


def test_transform_item_descriptions_extracts_latest_text():
    bronze = pd.DataFrame(
        [
            {
                "record_id": "MLB1",
                "ingested_at": "2026-09-10T10:00:00+00:00",
                "source": "mercado_livre_oauth",
                "payload": json.dumps({"id": "MLB1", "plain_text": "Descricao"}),
            }
        ]
    )

    silver = transform_item_descriptions(bronze)

    assert silver.loc[0, "item_id"] == "MLB1"
    assert silver.loc[0, "text_length"] == 9

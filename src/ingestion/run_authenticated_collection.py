import logging
from datetime import UTC, datetime

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
from src.storage.bronze import build_bronze_records, write_bronze_dataset
from src.utils.logging import configure_logging

logger = logging.getLogger(__name__)


def run_authenticated_collection() -> list[dict[str, object]]:
    settings = get_settings()
    ingested_at = datetime.now(UTC)
    token = load_valid_meli_token(settings)

    with MercadoLivreClient(
        base_url=settings.meli_base_url,
        timeout_seconds=settings.meli_timeout_seconds,
        max_retries=settings.meli_max_retries,
        rate_limit_seconds=settings.meli_rate_limit_seconds,
    ) as client:
        user = fetch_authenticated_user(client, token)
        seller_items = fetch_seller_item_ids(client, token, user_id=user["id"])
        item_details = fetch_item_details(
            client,
            token,
            item_ids=[item["id"] for item in seller_items if isinstance(item.get("id"), str)],
        )
        item_ids = [item["id"] for item in item_details if isinstance(item.get("id"), str)]
        item_descriptions = fetch_item_descriptions(client, token, item_ids=item_ids)
        item_price_snapshots = build_item_price_snapshots(item_details)

    records = build_bronze_records(
        [user],
        source="mercado_livre_oauth",
        endpoint="/users/me",
        ingested_at=ingested_at,
    )
    user_output = write_bronze_dataset(records, settings.data_dir, "authenticated_user", ingested_at)

    seller_item_records = build_bronze_records(
        seller_items,
        source="mercado_livre_oauth",
        endpoint="/users/{user_id}/items/search",
        ingested_at=ingested_at,
    )
    seller_items_output = write_bronze_dataset(
        seller_item_records,
        settings.data_dir,
        "seller_items",
        ingested_at,
    )
    item_detail_records = build_bronze_records(
        item_details,
        source="mercado_livre_oauth",
        endpoint="/items?ids={item_ids}",
        ingested_at=ingested_at,
    )
    item_details_output = write_bronze_dataset(
        item_detail_records,
        settings.data_dir,
        "item_details",
        ingested_at,
    )
    item_description_records = build_bronze_records(
        item_descriptions,
        source="mercado_livre_oauth",
        endpoint="/items/{item_id}/description",
        ingested_at=ingested_at,
    )
    item_descriptions_output = write_bronze_dataset(
        item_description_records,
        settings.data_dir,
        "item_descriptions",
        ingested_at,
    )
    item_price_records = build_bronze_records(
        item_price_snapshots,
        source="mercado_livre_oauth",
        endpoint="/items?ids={item_ids}:price_snapshot",
        ingested_at=ingested_at,
    )
    item_prices_output = write_bronze_dataset(
        item_price_records,
        settings.data_dir,
        "item_price_snapshots",
        ingested_at,
    )

    logger.info(
        "Authenticated Bronze dataset written",
        extra={
            "pipeline": "authenticated_collection",
            "task": "write_authenticated_datasets",
            "rows_processed": user_output["rows"]
            + seller_items_output["rows"]
            + item_details_output["rows"]
            + item_descriptions_output["rows"]
            + item_prices_output["rows"],
            "status": "success",
        },
    )
    return [
        user_output,
        seller_items_output,
        item_details_output,
        item_descriptions_output,
        item_prices_output,
    ]


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    outputs = run_authenticated_collection()
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()

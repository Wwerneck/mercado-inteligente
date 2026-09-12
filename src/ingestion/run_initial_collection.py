import argparse
import logging
from datetime import UTC, datetime

from src.config.settings import get_settings
from src.ingestion.api_client import MercadoLivreClient
from src.ingestion.categories import fetch_categories_by_id
from src.ingestion.domains import discover_domains
from src.storage.bronze import build_bronze_records, write_bronze_dataset
from src.utils.logging import configure_logging

logger = logging.getLogger(__name__)


def run_initial_collection(query: str) -> list[dict[str, object]]:
    settings = get_settings()
    ingested_at = datetime.now(UTC)
    outputs: list[dict[str, object]] = []

    with MercadoLivreClient(
        base_url=settings.meli_base_url,
        timeout_seconds=settings.meli_timeout_seconds,
        max_retries=settings.meli_max_retries,
        rate_limit_seconds=settings.meli_rate_limit_seconds,
    ) as client:
        domains = discover_domains(client, settings.meli_site_id, query)
        domain_records = build_bronze_records(
            domains,
            source="mercado_livre",
            endpoint=f"/sites/{settings.meli_site_id}/domain_discovery/search?q={query}",
            ingested_at=ingested_at,
        )
        outputs.append(write_bronze_dataset(domain_records, settings.data_dir, "domain_discovery", ingested_at))

        category_ids = [
            domain["category_id"]
            for domain in domains
            if isinstance(domain.get("category_id"), str)
        ]
        categories = fetch_categories_by_id(client, category_ids)
        category_records = build_bronze_records(
            categories,
            source="mercado_livre",
            endpoint="/categories/{category_id}",
            ingested_at=ingested_at,
        )
        outputs.append(write_bronze_dataset(category_records, settings.data_dir, "categories", ingested_at))

    for output in outputs:
        logger.info(
            "Bronze dataset written",
            extra={
                "pipeline": "phase_1_initial_collection",
                "task": f"write_{output['entity']}",
                "rows_processed": output["rows"],
                "status": "success",
            },
        )
    return outputs


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    parser = argparse.ArgumentParser(description="Coleta inicial real do Mercado Livre para Bronze.")
    parser.add_argument("--query", default="notebook", help="Termo de busca para produtos.")
    args = parser.parse_args()

    outputs = run_initial_collection(args.query)
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()

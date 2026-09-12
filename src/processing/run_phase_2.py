import logging

from src.analytics.gold import build_gold
from src.config.settings import get_settings
from src.processing.silver import build_silver
from src.utils.logging import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    silver_outputs = build_silver(settings.data_dir)
    for entity, path in silver_outputs.items():
        logger.info(
            "Silver dataset written",
            extra={
                "pipeline": "phase_2_lakehouse",
                "task": f"silver_{entity}",
                "status": "success",
            },
        )
        print({"layer": "silver", "entity": entity, "path": path})

    gold_outputs = build_gold(settings.data_dir)
    for entity, path in gold_outputs.items():
        logger.info(
            "Gold dataset written",
            extra={
                "pipeline": "phase_2_lakehouse",
                "task": f"gold_{entity}",
                "status": "success",
            },
        )
        print({"layer": "gold", "entity": entity, "path": path})


if __name__ == "__main__":
    main()


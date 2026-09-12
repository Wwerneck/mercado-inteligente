import argparse

from src.config.settings import get_settings
from src.orchestration.pipeline_tasks import run_full_pipeline
from src.utils.logging import configure_logging


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    parser = argparse.ArgumentParser(description="Executa o pipeline orquestrado da Fase 4.")
    parser.add_argument("--query", default=None)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    manifest = run_full_pipeline(query=args.query, run_id=args.run_id)
    print(manifest)


if __name__ == "__main__":
    main()

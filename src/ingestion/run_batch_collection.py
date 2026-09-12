import argparse

from src.config.settings import get_settings
from src.ingestion.run_initial_collection import run_initial_collection
from src.utils.logging import configure_logging

DEFAULT_QUERIES = [
    "notebook",
    "celular",
    "smart tv",
    "geladeira",
    "fone bluetooth",
    "cadeira gamer",
]


def configured_public_queries() -> list[str]:
    return get_settings().public_queries or DEFAULT_QUERIES


def run_batch_collection(queries: list[str]) -> list[dict[str, object]]:
    outputs: list[dict[str, object]] = []
    for query in queries:
        outputs.extend(run_initial_collection(query=query))
    return outputs


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    parser = argparse.ArgumentParser(description="Coleta em lote de consultas reais do Mercado Livre.")
    parser.add_argument("--query", action="append", dest="queries", help="Consulta adicional ou customizada.")
    args = parser.parse_args()

    queries = args.queries or configured_public_queries()
    outputs = run_batch_collection(queries)
    total_rows = sum(int(output["rows"]) for output in outputs)
    print({"queries": queries, "datasets": len(outputs), "rows": total_rows})


if __name__ == "__main__":
    main()

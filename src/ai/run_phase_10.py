import argparse

from src.ai.assistant import build_assistant
from src.config.settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Pergunte ao assistente semantico controlado.")
    parser.add_argument("question")
    args = parser.parse_args()

    settings = get_settings()
    assistant = build_assistant(settings.duckdb_path, settings.data_dir)
    response = assistant.answer(args.question)
    print(response.answer)
    print({"intent": response.intent, "sources": response.sources})


if __name__ == "__main__":
    main()


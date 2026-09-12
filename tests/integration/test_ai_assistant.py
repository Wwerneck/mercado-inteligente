from src.ai.assistant import build_assistant
from src.config.settings import get_settings


def test_assistant_answers_top_opportunities_from_real_artifact():
    settings = get_settings()
    assistant = build_assistant(settings.duckdb_path, settings.data_dir)

    response = assistant.answer("Quais categorias possuem maior Opportunity Score?")

    assert response.intent == "top_opportunities"
    assert "score" in response.answer.lower()
    assert response.data["total"] >= 2


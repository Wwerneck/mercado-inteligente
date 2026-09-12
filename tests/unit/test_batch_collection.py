from src.ingestion.run_batch_collection import DEFAULT_QUERIES


def test_default_batch_queries_cover_multiple_market_segments():
    assert "notebook" in DEFAULT_QUERIES
    assert "celular" in DEFAULT_QUERIES
    assert "geladeira" in DEFAULT_QUERIES
    assert len(DEFAULT_QUERIES) >= 6

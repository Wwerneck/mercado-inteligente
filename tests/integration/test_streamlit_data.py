from streamlit_app.data import (
    load_advanced_ml_metadata,
    load_category_metrics,
    load_marketplace_overview,
    load_ml_metadata,
    load_ml_scores,
    load_public_query_metrics,
)


def test_streamlit_data_loaders_return_real_data():
    categories = load_category_metrics()
    overview = load_marketplace_overview()
    ml_scores = load_ml_scores()
    query_metrics = load_public_query_metrics()
    ml_metadata = load_ml_metadata()
    advanced_ml_metadata = load_advanced_ml_metadata()

    assert len(categories) >= 2
    assert len(overview) == 1
    assert len(ml_scores) >= 2
    assert len(query_metrics) >= 1
    assert "opportunity_score" in ml_scores.columns
    assert "search_query" in query_metrics.columns
    assert "model_version" in ml_metadata
    assert "readiness" in advanced_ml_metadata

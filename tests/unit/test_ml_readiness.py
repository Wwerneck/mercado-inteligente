import pandas as pd

from src.ml.evaluation.readiness import (
    evaluate_clustering_readiness,
    evaluate_forecasting_readiness,
)


def test_readiness_blocks_small_clustering_dataset():
    result = evaluate_clustering_readiness(pd.DataFrame([{"a": 1}, {"a": 2}]))

    assert result.ready is False
    assert "Requires at least" in result.reason


def test_readiness_blocks_short_forecasting_history():
    result = evaluate_forecasting_readiness(pd.DataFrame({"snapshot_date_key": [20260910]}))

    assert result.ready is False
    assert "temporal snapshots" in result.reason


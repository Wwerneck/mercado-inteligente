import pandas as pd

from src.ml.training.forecasting import build_naive_forecast


def test_build_naive_forecast_uses_previous_snapshot():
    frame = pd.DataFrame(
        [
            {"category_id": "A", "snapshot_date_key": 20260910, "opportunity_score": 10.0},
            {"category_id": "A", "snapshot_date_key": 20260911, "opportunity_score": 20.0},
        ]
    )

    forecast, metadata = build_naive_forecast(frame)

    assert forecast.loc[0, "forecast_value"] == 10.0
    assert metadata["model_name"] == "naive_previous_snapshot"


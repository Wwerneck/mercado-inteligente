import pandas as pd


def build_naive_forecast(
    frame: pd.DataFrame,
    target_column: str = "opportunity_score",
) -> tuple[pd.DataFrame, dict[str, object]]:
    ordered = frame.sort_values(["category_id", "snapshot_date_key"]).copy()
    ordered["forecast_value"] = ordered.groupby("category_id")[target_column].shift(1)
    forecast = ordered.dropna(subset=["forecast_value"]).reset_index(drop=True).copy()
    forecast["model_name"] = "naive_previous_snapshot"
    metadata = {
        "model_name": "naive_previous_snapshot",
        "target_column": target_column,
        "rows": len(forecast),
        "evaluation": "Previous snapshot baseline. Requires real temporal history.",
    }
    return forecast, metadata

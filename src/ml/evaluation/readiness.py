from dataclasses import dataclass

import pandas as pd

MIN_CLUSTERING_ROWS = 5
MIN_FORECAST_SNAPSHOTS = 14


@dataclass(frozen=True)
class ReadinessResult:
    name: str
    ready: bool
    reason: str


def evaluate_clustering_readiness(frame: pd.DataFrame) -> ReadinessResult:
    rows = len(frame)
    if rows < MIN_CLUSTERING_ROWS:
        return ReadinessResult(
            name="clustering",
            ready=False,
            reason=f"Requires at least {MIN_CLUSTERING_ROWS} rows; current dataset has {rows}.",
        )
    return ReadinessResult("clustering", True, "Dataset has enough rows for baseline clustering.")


def evaluate_forecasting_readiness(frame: pd.DataFrame) -> ReadinessResult:
    if frame.empty or "snapshot_date_key" not in frame.columns:
        return ReadinessResult("forecasting", False, "Dataset has no snapshot_date_key column.")
    snapshot_count = int(frame["snapshot_date_key"].nunique())
    if snapshot_count < MIN_FORECAST_SNAPSHOTS:
        return ReadinessResult(
            name="forecasting",
            ready=False,
            reason=(
                f"Requires at least {MIN_FORECAST_SNAPSHOTS} temporal snapshots; "
                f"current dataset has {snapshot_count}."
            ),
        )
    return ReadinessResult("forecasting", True, "Dataset has enough temporal snapshots.")


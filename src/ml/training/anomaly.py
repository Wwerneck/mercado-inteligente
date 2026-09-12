import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.ml.features.category_features import FEATURE_COLUMNS

MIN_ISOLATION_FOREST_ROWS = 30


def detect_category_anomalies(features: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    frame = features.copy()
    values = frame[FEATURE_COLUMNS].fillna(0.0).to_numpy(dtype=float)

    metadata: dict[str, object] = {
        "model_name": "category_anomaly_detection",
        "methods": ["z_score", "iqr"],
        "rows": len(frame),
        "isolation_forest_used": False,
        "limitation": None,
    }

    if len(frame) == 0:
        frame["anomaly_score"] = []
        frame["is_anomaly"] = []
        frame["anomaly_type"] = []
        return frame, metadata

    coverage = frame["catalog_coverage_score"].fillna(0).to_numpy(dtype=float)
    std = coverage.std(ddof=0)
    zscore = np.divide(
        coverage - coverage.mean(),
        std,
        out=np.zeros_like(coverage, dtype=float),
        where=std > 0,
    )
    q1, q3 = np.percentile(coverage, [25, 75])
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    iqr_anomaly = (coverage < lower) | (coverage > upper)

    frame["zscore_abs"] = np.abs(zscore)
    frame["iqr_anomaly"] = iqr_anomaly

    if len(frame) >= MIN_ISOLATION_FOREST_ROWS:
        model = IsolationForest(random_state=42, contamination="auto")
        model.fit(values)
        isolation_scores = -model.score_samples(values)
        frame["isolation_score"] = isolation_scores
        metadata["methods"].append("isolation_forest")
        metadata["isolation_forest_used"] = True
    else:
        frame["isolation_score"] = 0.0
        metadata["limitation"] = (
            "Isolation Forest requires at least "
            f"{MIN_ISOLATION_FOREST_ROWS} rows; current dataset has {len(frame)}."
        )

    frame["anomaly_score"] = np.round(
        np.maximum(frame["zscore_abs"].to_numpy(dtype=float) * 20, frame["isolation_score"].to_numpy(dtype=float)),
        4,
    )
    frame["is_anomaly"] = (frame["zscore_abs"] >= 3.0) | frame["iqr_anomaly"]
    frame["anomaly_type"] = np.where(
        frame["is_anomaly"],
        np.where(coverage >= upper, "high_catalog_coverage", "low_catalog_coverage"),
        "none",
    )
    return frame, metadata


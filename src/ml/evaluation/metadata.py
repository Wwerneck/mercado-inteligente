from datetime import UTC, datetime
from typing import Any


def build_model_metadata(
    anomaly_metadata: dict[str, Any],
    feature_columns: list[str],
    output_rows: int,
) -> dict[str, Any]:
    return {
        "model_version": "category_ml_baseline_v1",
        "trained_at": datetime.now(UTC).isoformat(),
        "problem": "Detect category-level anomalies and produce marketplace opportunity scores.",
        "features": feature_columns,
        "metrics": {
            "output_rows": output_rows,
            "anomaly_count": anomaly_metadata.get("anomaly_count", 0),
        },
        "parameters": {
            "random_state": 42,
            "opportunity_score_scale": "0-100",
        },
        "anomaly_detection": anomaly_metadata,
    }


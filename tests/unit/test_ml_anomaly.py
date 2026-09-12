import pandas as pd

from src.ml.features.category_features import FEATURE_COLUMNS
from src.ml.training.anomaly import detect_category_anomalies


def test_detect_category_anomalies_documents_small_sample_limitation():
    frame = pd.DataFrame(
        [
            {
                "category_id": "A",
                "category_name": "A",
                "snapshot_date_key": 20260910,
                "snapshot_date": "2026-09-10",
                "total_items_log": 1.0,
                "domain_count": 1,
                "category_depth": 1,
                "catalog_coverage_score": 100.0,
                "items_share": 1.0,
                "competition_density": 0.01,
            }
        ],
        columns=["category_id", "category_name", "snapshot_date_key", "snapshot_date", *FEATURE_COLUMNS],
    )

    scored, metadata = detect_category_anomalies(frame)

    assert "anomaly_score" in scored.columns
    assert metadata["isolation_forest_used"] is False
    assert metadata["limitation"] is not None


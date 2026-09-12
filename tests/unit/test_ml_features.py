import pandas as pd

from src.ml.features.category_features import build_category_features


def test_build_category_features_uses_real_numeric_inputs():
    frame = pd.DataFrame(
        [
            {
                "category_id": "A",
                "category_name": "A",
                "snapshot_date_key": 20260910,
                "snapshot_date": "2026-09-10",
                "domain_count": 1,
                "total_items_in_this_category": 100,
                "category_depth": 2,
                "catalog_coverage_score": 100.0,
            }
        ]
    )

    features = build_category_features(frame)

    assert features.loc[0, "items_share"] == 1
    assert features.loc[0, "competition_density"] == 0.01


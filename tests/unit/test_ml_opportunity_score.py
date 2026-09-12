import pandas as pd

from src.ml.inference.opportunity_score import calculate_opportunity_score


def test_calculate_opportunity_score_returns_ranked_scores():
    frame = pd.DataFrame(
        [
            {
                "category_id": "A",
                "catalog_coverage_score": 100.0,
                "competition_density": 0.01,
                "category_depth": 2,
                "is_anomaly": False,
            },
            {
                "category_id": "B",
                "catalog_coverage_score": 50.0,
                "competition_density": 0.10,
                "category_depth": 1,
                "is_anomaly": True,
            },
        ]
    )

    scored = calculate_opportunity_score(frame)

    assert scored.iloc[0]["category_id"] == "A"
    assert scored["opportunity_score"].between(0, 100).all()


from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class OpportunityWeights:
    catalog_coverage: float = 0.35
    low_competition_density: float = 0.30
    category_depth: float = 0.15
    stability: float = 0.20

    def normalized(self) -> "OpportunityWeights":
        total = (
            self.catalog_coverage
            + self.low_competition_density
            + self.category_depth
            + self.stability
        )
        if total <= 0:
            raise ValueError("Opportunity score weights must sum to a positive value.")
        return OpportunityWeights(
            catalog_coverage=self.catalog_coverage / total,
            low_competition_density=self.low_competition_density / total,
            category_depth=self.category_depth / total,
            stability=self.stability / total,
        )


def _min_max_score(values: pd.Series, invert: bool = False) -> np.ndarray:
    array = values.fillna(0).to_numpy(dtype=float)
    min_value = array.min() if len(array) else 0
    max_value = array.max() if len(array) else 0
    if max_value == min_value:
        score = np.full_like(array, 50.0, dtype=float)
    else:
        score = ((array - min_value) / (max_value - min_value)) * 100
    return 100 - score if invert else score


def calculate_opportunity_score(
    scored_features: pd.DataFrame,
    weights: OpportunityWeights | None = None,
) -> pd.DataFrame:
    normalized_weights = (weights or OpportunityWeights()).normalized()
    frame = scored_features.copy()

    coverage_component = frame["catalog_coverage_score"].fillna(0).to_numpy(dtype=float)
    competition_component = _min_max_score(frame["competition_density"], invert=True)
    depth_component = _min_max_score(frame["category_depth"], invert=False)
    stability_component = np.where(frame["is_anomaly"], 0.0, 100.0)

    frame["opportunity_score"] = np.round(
        coverage_component * normalized_weights.catalog_coverage
        + competition_component * normalized_weights.low_competition_density
        + depth_component * normalized_weights.category_depth
        + stability_component * normalized_weights.stability,
        2,
    )
    frame["opportunity_rank"] = frame["opportunity_score"].rank(method="dense", ascending=False).astype("int64")
    return frame.sort_values(["opportunity_rank", "category_id"]).reset_index(drop=True)


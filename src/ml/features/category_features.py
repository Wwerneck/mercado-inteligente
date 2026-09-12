import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "total_items_log",
    "domain_count",
    "category_depth",
    "catalog_coverage_score",
    "items_share",
    "competition_density",
]


def build_category_features(category_metrics: pd.DataFrame) -> pd.DataFrame:
    frame = category_metrics.copy()
    total_items = frame["total_items_in_this_category"].fillna(0).to_numpy(dtype=float)
    total_market_items = total_items.sum()

    frame["total_items_log"] = np.log1p(total_items)
    frame["items_share"] = np.divide(
        total_items,
        total_market_items,
        out=np.zeros_like(total_items, dtype=float),
        where=total_market_items > 0,
    )
    frame["competition_density"] = np.divide(
        frame["domain_count"].to_numpy(dtype=float),
        np.maximum(total_items, 1.0),
    )

    return frame[
        [
            "category_id",
            "category_name",
            "snapshot_date_key",
            "snapshot_date",
            *FEATURE_COLUMNS,
        ]
    ]


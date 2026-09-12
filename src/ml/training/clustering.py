import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from src.ml.features.category_features import FEATURE_COLUMNS


def fit_category_clusters(frame: pd.DataFrame, random_state: int = 42) -> tuple[pd.DataFrame, dict[str, object]]:
    features = frame[FEATURE_COLUMNS].fillna(0.0).to_numpy(dtype=float)
    scaled = StandardScaler().fit_transform(features)
    max_k = min(6, len(frame) - 1)
    candidates: list[dict[str, float | int]] = []

    for k in range(2, max_k + 1):
        model = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = model.fit_predict(scaled)
        score = float(silhouette_score(scaled, labels)) if len(set(labels)) > 1 else -1.0
        candidates.append({"k": k, "silhouette_score": score})

    best = max(candidates, key=lambda item: item["silhouette_score"])
    final_model = KMeans(n_clusters=int(best["k"]), random_state=random_state, n_init=10)
    result = frame.copy()
    result["cluster_id"] = final_model.fit_predict(scaled)
    distances = final_model.transform(scaled)
    result["cluster_distance"] = np.round(distances.min(axis=1), 4)
    result["cluster_label"] = result["cluster_id"].map(lambda value: f"cluster_{value}")

    metadata = {
        "model_name": "kmeans_category_clustering",
        "selected_k": int(best["k"]),
        "selection_metric": "silhouette_score",
        "candidates": candidates,
        "rows": len(frame),
        "random_state": random_state,
    }
    return result, metadata


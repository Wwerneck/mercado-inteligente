import json
import logging

import pandas as pd

from src.config.settings import get_settings
from src.ml.evaluation.readiness import (
    evaluate_clustering_readiness,
    evaluate_forecasting_readiness,
)
from src.ml.training.clustering import fit_category_clusters
from src.ml.training.forecasting import build_naive_forecast
from src.utils.logging import configure_logging

logger = logging.getLogger(__name__)


def run_advanced_ml_pipeline() -> dict[str, str]:
    settings = get_settings()
    scores_path = settings.data_dir / "gold" / "ml_category_scores.parquet"
    scores = pd.read_parquet(scores_path)
    features = scores.copy()

    clustering_readiness = evaluate_clustering_readiness(features)
    forecasting_readiness = evaluate_forecasting_readiness(scores)
    metadata: dict[str, object] = {
        "phase": "phase_7_advanced_ml",
        "readiness": {
            clustering_readiness.name: clustering_readiness.__dict__,
            forecasting_readiness.name: forecasting_readiness.__dict__,
        },
        "outputs": {},
    }

    if clustering_readiness.ready:
        clustered, clustering_metadata = fit_category_clusters(features)
        cluster_path = settings.data_dir / "gold" / "ml_category_clusters.parquet"
        clustered.to_parquet(cluster_path, index=False)
        metadata["outputs"]["clusters"] = str(cluster_path)
        metadata["clustering"] = clustering_metadata

    if forecasting_readiness.ready:
        forecast, forecast_metadata = build_naive_forecast(scores)
        forecast_path = settings.data_dir / "gold" / "ml_category_forecast.parquet"
        forecast.to_parquet(forecast_path, index=False)
        metadata["outputs"]["forecast"] = str(forecast_path)
        metadata["forecasting"] = forecast_metadata

    metadata_path = settings.data_dir / "gold" / "ml_advanced_metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(
        "Advanced ML readiness evaluated",
        extra={
            "pipeline": "phase_7_advanced_ml",
            "task": "readiness",
            "status": "success",
        },
    )
    return {"metadata": str(metadata_path), **metadata["outputs"]}


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    print(run_advanced_ml_pipeline())


if __name__ == "__main__":
    main()

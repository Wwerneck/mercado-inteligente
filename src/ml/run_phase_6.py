import logging

import duckdb

from src.config.settings import get_settings
from src.ml.evaluation.metadata import build_model_metadata
from src.ml.features.category_features import FEATURE_COLUMNS, build_category_features
from src.ml.inference.opportunity_score import calculate_opportunity_score
from src.ml.registry.artifacts import write_ml_outputs
from src.ml.training.anomaly import detect_category_anomalies
from src.utils.logging import configure_logging

logger = logging.getLogger(__name__)


def load_category_metrics_from_dbt(duckdb_path: str):
    with duckdb.connect(duckdb_path) as connection:
        return connection.execute("select * from main_marts.mart_category_metrics").fetchdf()


def run_ml_pipeline() -> dict[str, str]:
    settings = get_settings()
    category_metrics = load_category_metrics_from_dbt(str(settings.duckdb_path))
    features = build_category_features(category_metrics)
    anomaly_scores, anomaly_metadata = detect_category_anomalies(features)
    opportunity_scores = calculate_opportunity_score(anomaly_scores)
    anomaly_metadata["anomaly_count"] = int(opportunity_scores["is_anomaly"].sum())
    metadata = build_model_metadata(
        anomaly_metadata=anomaly_metadata,
        feature_columns=FEATURE_COLUMNS,
        output_rows=len(opportunity_scores),
    )
    outputs = write_ml_outputs(opportunity_scores, metadata, settings.data_dir)
    logger.info(
        "ML baseline outputs written",
        extra={
            "pipeline": "phase_6_ml_baseline",
            "task": "write_ml_outputs",
            "rows_processed": len(opportunity_scores),
            "status": "success",
        },
    )
    return outputs


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    print(run_ml_pipeline())


if __name__ == "__main__":
    main()


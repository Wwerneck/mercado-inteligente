from __future__ import annotations

from datetime import UTC, datetime, timedelta

try:
    from airflow.decorators import dag, task
except ModuleNotFoundError:
    dag = None
    task = None


if dag and task:

    @dag(
        dag_id="mercado_intelligence_pipeline",
        description="Ingestao, lakehouse e publicacao analitica do Mercado Intelligence AI.",
        start_date=datetime(2026, 9, 10, tzinfo=UTC),
        schedule="@daily",
        catchup=False,
        default_args={
            "owner": "mercado-intelligence-ai",
            "retries": 2,
            "retry_delay": timedelta(minutes=3),
        },
        tags=["mercado-livre", "data-engineering", "lakehouse"],
        max_active_runs=1,
    )
    def mercado_intelligence_pipeline():
        @task
        def extract_marketplace_data():
            from src.orchestration.pipeline_tasks import extract_marketplace_data

            return extract_marketplace_data()

        @task
        def extract_authenticated_marketplace_data():
            from src.orchestration.pipeline_tasks import extract_authenticated_marketplace_data

            return extract_authenticated_marketplace_data()

        @task
        def validate_raw_data():
            from src.orchestration.pipeline_tasks import validate_raw_data

            return validate_raw_data()

        @task
        def transform_silver():
            from src.orchestration.pipeline_tasks import transform_silver

            return transform_silver()

        @task
        def data_quality_checks():
            from src.orchestration.pipeline_tasks import data_quality_checks

            return data_quality_checks()

        @task
        def build_gold():
            from src.orchestration.pipeline_tasks import build_gold_layer

            return build_gold_layer()

        @task
        def publish_to_warehouse():
            from src.orchestration.pipeline_tasks import publish_to_warehouse

            return publish_to_warehouse()

        @task
        def generate_ml_results():
            from src.orchestration.pipeline_tasks import generate_ml_results

            return generate_ml_results()

        @task
        def generate_advanced_ml_results():
            from src.orchestration.pipeline_tasks import generate_advanced_ml_results

            return generate_advanced_ml_results()

        raw = extract_marketplace_data()
        authenticated_raw = extract_authenticated_marketplace_data()
        validated = validate_raw_data()
        silver = transform_silver()
        quality = data_quality_checks()
        gold = build_gold()
        warehouse = publish_to_warehouse()
        ml_results = generate_ml_results()
        advanced_ml_results = generate_advanced_ml_results()

        (
            raw
            >> authenticated_raw
            >> validated
            >> silver
            >> quality
            >> gold
            >> warehouse
            >> ml_results
            >> advanced_ml_results
        )

    mercado_intelligence_pipeline()

import importlib.util
from pathlib import Path


def test_airflow_dag_file_is_importable_without_airflow_installed():
    dag_path = Path("airflow/dags/mercado_intelligence_pipeline.py")
    spec = importlib.util.spec_from_file_location("mercado_intelligence_pipeline", dag_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)


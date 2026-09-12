# Airflow

A Fase 4 adiciona a DAG `mercado_intelligence_pipeline`.

Fluxo:

```text
extract_marketplace_data
  -> extract_authenticated_marketplace_data
  -> validate_raw_data
  -> transform_silver
  -> data_quality_checks
  -> build_gold
  -> publish_to_warehouse
  -> generate_ml_results
  -> generate_advanced_ml_results
```

As tarefas chamam codigo real do projeto em `src/orchestration/pipeline_tasks.py`.

A coleta autenticada e opcional: quando `MELI_TOKEN_STORE_PATH` nao existe, a task retorna `skipped` e a DAG continua para Silver, Gold, warehouse e ML. Quando o token existe, ela coleta dados do seller autenticado antes da transformacao Silver.

No ambiente local atual, o Apache Airflow nao esta instalado. Por isso a DAG usa imports condicionais para continuar importavel nos testes. Em ambiente com Airflow instalado, o arquivo registra a DAG normalmente.

Execucao local equivalente:

```bash
python -m src.orchestration.run_phase_4 --query notebook
```

Cada execucao grava um manifesto em:

```text
data/pipeline_runs/
```

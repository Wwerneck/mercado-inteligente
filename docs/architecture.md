# Arquitetura

O projeto implementa uma plataforma local de engenharia de dados, ML e IA para inteligencia de marketplace.

Fluxo atual:

```text
Mercado Livre API publica/OAuth
  -> Airflow/Python ingestion
  -> Bronze JSONL/Parquet
  -> Silver Parquet
  -> Gold Parquet
  -> DuckDB/PostgreSQL dimensional
  -> dbt marts
  -> FastAPI / Streamlit / Assistente IA
```

O fluxo OAuth e opcional. Sem token salvo, a coleta autenticada e ignorada e o pipeline publico continua funcionando. Com token salvo, dados de seller e anuncios entram em Bronze, Silver, Gold, warehouse dimensional, dbt, API, dashboard e assistente.

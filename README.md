# Mercado Intelligence AI

Plataforma de Engenharia de Dados, Machine Learning e IA para inteligencia de marketplace com dados publicos do Mercado Livre. O fluxo principal nao exige conta vendedora.

## Links

- Dashboard Streamlit Cloud: https://mercado-inteligente.streamlit.app/
- Repositorio GitHub: https://github.com/Wwerneck/mercado-inteligente

## Problema de negocio

Marketplace operators precisam acompanhar categorias, concorrencia, cobertura de catalogo, oportunidades e anomalias de forma rastreavel. Este projeto demonstra uma arquitetura completa para coletar, transformar, modelar, disponibilizar e explicar dados do Mercado Livre sem inventar informacoes.

## Arquitetura

```text
Mercado Livre API
  -> Python ingestion
  -> Bronze JSONL/Parquet
  -> Silver Parquet
  -> Gold Parquet
  -> DuckDB/PostgreSQL
  -> dbt marts
  -> ML results
  -> FastAPI / Streamlit / AI Assistant
```

## Stack

Python, Pandas, NumPy, PyArrow, DuckDB, PostgreSQL, Airflow, dbt, FastAPI, Streamlit, scikit-learn, Docker e GitHub Actions.

## Implementado

- ingestao real com endpoints publicos oficiais;
- Data Lake Bronze/Silver/Gold;
- qualidade de dados;
- modelo dimensional;
- DuckDB local e DDL PostgreSQL;
- DAG Airflow e runner local;
- imagem Airflow customizada com dependencias do projeto;
- projeto dbt com staging, intermediate e marts;
- coleta publica em lote configuravel por `MELI_PUBLIC_QUERIES`;
- fluxo OAuth Mercado Livre opcional para contas vendedoras, com persistencia criptografada;
- ML basico, Opportunity Score e readiness de ML avancado;
- API REST;
- dashboard Streamlit;
- assistente analitico controlado;
- observabilidade de pipeline;
- Docker Compose;
- CI com lint, testes e dbt parse;
- deploy publico no Streamlit Cloud.

## Como executar

```bash
python -m venv .venv
pip install -r requirements.txt
python -m src.orchestration.run_phase_4
cd dbt && dbt run --profiles-dir . && dbt test --profiles-dir .
uvicorn src.api.main:app --reload
streamlit run streamlit_app/app.py
python -m src.ai.run_phase_10 "Quais categorias possuem maior Opportunity Score?"
pytest
```

## Docker

```bash
docker compose up --build
```

## Estrutura do projeto

```text
src/
  config/
  analytics/
  database/
  orchestration/
  ingestion/
  processing/
  storage/
  utils/
data/
  bronze/
  silver/
  gold/
dbt/
airflow/
streamlit_app/
tests/
  unit/
docs/
```

## Resultados atuais

- Categorias monitoradas: 2
- Dominios monitorados: 2
- Categorias monitoradas: 24
- Dominios distintos monitorados: 17
- Itens nas categorias: 617.558
- Melhor Opportunity Score: Geladeiras Termicas, 75.94
- Testes automatizados: 32 passando antes da Fase 11

## Limitacoes

O pipeline de coleta ainda usa endpoints publicos por padrao. Em setembro de 2026, endpoints como `/sites/MLB/search` e `/products/search` podem retornar `403 Forbidden` por politica da API. Por isso, a Fase 1 coleta dados reais via `/sites/MLB/domain_discovery/search` e `/categories/{category_id}`.

A API expoe o fluxo OAuth Authorization Code como modulo opcional para contas vendedoras. O fluxo principal de engenharia de dados usa dados publicos configurados por `MELI_PUBLIC_QUERIES`.

Clustering ja e executado com a base ampliada. Forecasting permanece condicionado a historico temporal real.

## Roadmap

- ampliar dashboards publicos por termos, categorias, dominios e tendencias;
- coleta autenticada opcional de reputacao, visitas e anuncios quando houver conta vendedora;
- forecasting temporal;
- evoluir o deploy em cloud com cache persistente e observabilidade;
- observabilidade com metricas externas.

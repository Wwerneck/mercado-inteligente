# Streamlit

A Fase 9 adiciona dashboard Streamlit para consumo visual dos marts e resultados de ML.

## Executar

```bash
streamlit run streamlit_app/app.py
```

## Abas

- Overview
- Categorias
- Oportunidades
- Seller
- Machine Learning
- Pipeline
- OAuth
- Qualidade
- Assistente

O app le dados diretamente do DuckDB, dos marts dbt e dos artefatos em `data/gold`.

## OAuth

A aba OAuth permite:

- verificar se `MELI_CLIENT_ID`, `MELI_CLIENT_SECRET` e `MELI_REDIRECT_URI` estao configurados;
- ver se existe token salvo em `MELI_TOKEN_STORE_PATH`;
- gerar a URL de autorizacao do Mercado Livre;
- salvar o token a partir de `code` e `state` retornados pelo fluxo OAuth;
- visualizar somente tokens mascarados.

Depois de salvar o token, execute o pipeline orquestrado para popular seller, anuncios e metricas:

```bash
python -m src.orchestration.run_phase_4 --query notebook
cd dbt
dbt run --profiles-dir .
dbt test --profiles-dir .
```

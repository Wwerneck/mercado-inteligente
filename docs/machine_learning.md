# Machine Learning

A Fase 6 cria uma camada inicial de ML baseada nos dados reais atualmente disponiveis.

## Problema

Detectar comportamentos fora do padrao em categorias e gerar um `Marketplace Opportunity Score`.

## Dados usados

Fonte atual:

```text
main_marts.mart_category_metrics
```

Como os endpoints publicos de produtos/anuncios retornaram `403 Forbidden`, ainda nao existe historico de precos suficiente para previsao ou anomalia de preco. Esta fase usa metricas reais de categoria.

## Features

- `total_items_log`
- `domain_count`
- `category_depth`
- `catalog_coverage_score`
- `items_share`
- `competition_density`

## Anomalias

Metodos implementados:

- Z-Score
- IQR
- Isolation Forest, apenas quando houver pelo menos 30 linhas

Com o dataset atual de 24 categorias, Z-Score e IQR sao usados como baseline interpretavel. Isolation Forest permanece condicionado a pelo menos 30 linhas.

## Opportunity Score

Escala: 0 a 100.

Componentes:

- cobertura de catalogo;
- baixa densidade competitiva;
- profundidade da categoria;
- estabilidade, penalizando anomalias.

Pesos padrao:

- catalog_coverage: 0.35
- low_competition_density: 0.30
- category_depth: 0.15
- stability: 0.20

## Artefatos

```text
data/gold/ml_category_scores.parquet
data/gold/ml_model_metadata.json
```

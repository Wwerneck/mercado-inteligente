# Machine Learning Avancado

A Fase 7 adiciona clustering e forecasting de forma condicionada a dados suficientes.

## Clustering

Modelo planejado:

- KMeans
- escolha de `k` por silhouette score

Condicao minima atual:

- pelo menos 5 linhas

## Forecasting

Modelo inicial:

- baseline ingenuo usando o snapshot anterior

Condicao minima atual:

- pelo menos 14 snapshots temporais reais

## Estado atual

O dataset atual possui 24 categorias e 1 snapshot. Clustering ja esta habilitado e gera grupos com KMeans. Forecasting segue bloqueado porque exige pelo menos 14 snapshots temporais reais.

Artefato:

```text
data/gold/ml_advanced_metadata.json
data/gold/ml_category_clusters.parquet
```

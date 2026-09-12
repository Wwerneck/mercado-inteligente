# dbt

A Fase 5 adiciona um projeto dbt usando DuckDB como adapter.

Fonte:

```text
analytics.dim_category
analytics.dim_domain
analytics.dim_date
analytics.fact_category_snapshot
analytics.fact_marketplace_overview
analytics.dim_seller
analytics.dim_item
analytics.fact_seller_item_snapshot
```

Camadas:

```text
staging -> intermediate -> marts
```

Comandos:

```bash
cd dbt
dbt parse --profiles-dir .
dbt run --profiles-dir .
dbt test --profiles-dir .
```

Marts:

- `mart_category_metrics`
- `mart_marketplace_overview`
- `mart_seller_item_metrics`
- `mart_seller_items`

Modelos autenticados:

- `stg_item_details`: normaliza o Parquet Silver de detalhes dos anuncios.
- `mart_seller_item_metrics`: agrega anuncios por seller, categoria e status.
- `mart_seller_items`: expoe detalhes dos anuncios autenticados por snapshot.
- Metricas avancadas do seller incluem `sell_through_rate`, `price_spread`, `paused_item_count` e `zero_sales_stock_count`.

Testes adicionais:

- `assert_seller_item_prices_non_negative`
- `assert_seller_item_quantities_non_negative`
- `assert_seller_item_sell_through_between_0_and_100`

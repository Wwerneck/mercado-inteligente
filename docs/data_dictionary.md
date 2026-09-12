# Dicionario de Dados

## Silver categories

| Coluna | Tipo | Descricao | Origem | Nullable | Camada |
|---|---|---|---|---|---|
| category_id | string | ID da categoria | Mercado Livre `/categories/{id}` | nao | Silver |
| category_name | string | Nome da categoria | Mercado Livre | nao | Silver |
| total_items_in_this_category | integer | Total informado pela API | Mercado Livre | sim | Silver |
| path_from_root | string | Caminho hierarquico da categoria | Mercado Livre | sim | Silver |
| children_categories_count | integer | Quantidade de subcategorias | derivado | nao | Silver |

## Gold category_metrics

| Coluna | Tipo | Descricao | Origem | Nullable | Camada |
|---|---|---|---|---|---|
| category_id | string | ID da categoria | Silver | nao | Gold |
| domain_count | integer | Dominios descobertos associados | Silver domain_discovery | nao | Gold |
| catalog_coverage_score | float | Score 0-100 relativo ao maior volume monitorado | derivado | nao | Gold |

## Gold seller_item_metrics

| Coluna | Tipo | Descricao | Origem | Nullable | Camada |
|---|---|---|---|---|---|
| seller_id | string | ID do seller autenticado | Silver item_details | sim | Gold |
| category_id | string | Categoria dos anuncios agregados | Silver item_details | sim | Gold |
| status | string | Status dos anuncios agregados | Silver item_details | nao | Gold |
| item_count | integer | Quantidade de anuncios distintos | derivado | nao | Gold |
| active_item_count | integer | Quantidade de anuncios ativos | derivado | nao | Gold |
| avg_price | float | Preco medio dos anuncios | derivado | sim | Gold |
| min_price | float | Menor preco dos anuncios | derivado | sim | Gold |
| max_price | float | Maior preco dos anuncios | derivado | sim | Gold |
| total_available_quantity | integer | Soma do estoque disponivel | derivado | nao | Gold |
| total_sold_quantity | integer | Soma da quantidade vendida | derivado | nao | Gold |
| sell_through_rate | float | Percentual vendido sobre vendido + estoque disponivel | derivado | nao | Gold |
| price_spread | float | Diferenca entre maior e menor preco no agrupamento | derivado | sim | Gold |
| paused_item_count | integer | Quantidade de anuncios pausados | derivado | nao | Gold |
| zero_sales_stock_count | integer | Quantidade de anuncios com estoque e sem venda registrada | derivado | nao | Gold |
| latest_ingestion_at | timestamp | Ingestao mais recente considerada | Silver item_details | sim | Gold |

## dbt mart_seller_items

| Coluna | Tipo | Descricao | Origem | Nullable | Camada |
|---|---|---|---|---|---|
| item_id | string | ID do anuncio | Warehouse dim_item | nao | dbt mart |
| title | string | Titulo do anuncio | Warehouse dim_item | sim | dbt mart |
| seller_id | string | Seller do anuncio | Warehouse dim_item | sim | dbt mart |
| category_id | string | Categoria do anuncio | Warehouse dim_item | sim | dbt mart |
| status | string | Status do anuncio no snapshot | Warehouse fact_seller_item_snapshot | nao | dbt mart |
| price | float | Preco no snapshot | Warehouse fact_seller_item_snapshot | sim | dbt mart |
| available_quantity | integer | Estoque disponivel no snapshot | Warehouse fact_seller_item_snapshot | sim | dbt mart |
| sold_quantity | integer | Quantidade vendida no snapshot | Warehouse fact_seller_item_snapshot | sim | dbt mart |
| snapshot_date_key | integer | Chave da data do snapshot | Warehouse fact_seller_item_snapshot | nao | dbt mart |
| snapshot_date | string | Data do snapshot | Warehouse dim_date | sim | dbt mart |

## Silver domain_discovery

| Coluna | Tipo | Descricao | Origem | Nullable | Camada |
|---|---|---|---|---|---|
| domain_category_id | string | Chave da associacao dominio + categoria | derivado | nao | Silver |
| domain_id | string | ID do dominio retornado pela API | Mercado Livre | nao | Silver |
| category_id | string | ID da categoria sugerida para a consulta | Mercado Livre | nao | Silver |
| search_query | string | Consulta que originou a descoberta | endpoint Bronze | sim | Silver |

## Silver item_details

| Coluna | Tipo | Descricao | Origem | Nullable | Camada |
|---|---|---|---|---|---|
| item_id | string | ID do anuncio | Mercado Livre `/items` | nao | Silver |
| title | string | Titulo do anuncio | Mercado Livre | sim | Silver |
| price | float | Preco atual do anuncio | Mercado Livre | sim | Silver |
| currency_id | string | Moeda do preco | Mercado Livre | sim | Silver |
| available_quantity | integer | Estoque disponivel informado pela API | Mercado Livre | sim | Silver |
| sold_quantity | integer | Quantidade vendida informada pela API | Mercado Livre | sim | Silver |
| status | string | Status do anuncio | Mercado Livre | sim | Silver |
| condition | string | Condicao do item | Mercado Livre | sim | Silver |
| category_id | string | Categoria do anuncio | Mercado Livre | sim | Silver |
| listing_type_id | string | Tipo de anuncio | Mercado Livre | sim | Silver |
| permalink | string | URL publica do anuncio | Mercado Livre | sim | Silver |
| seller_id | string | ID do seller | Mercado Livre | sim | Silver |
| site_id | string | Site Mercado Livre | Mercado Livre | sim | Silver |
| date_created | timestamp | Data de criacao do anuncio | Mercado Livre | sim | Silver |
| last_updated | timestamp | Ultima atualizacao do anuncio | Mercado Livre | sim | Silver |

## Warehouse dim_seller

| Coluna | Tipo | Descricao | Origem | Nullable | Camada |
|---|---|---|---|---|---|
| seller_id | string | ID do seller autenticado | Silver item_details | nao | Warehouse |

## Warehouse dim_item

| Coluna | Tipo | Descricao | Origem | Nullable | Camada |
|---|---|---|---|---|---|
| item_id | string | ID do anuncio | Silver item_details | nao | Warehouse |
| title | string | Titulo do anuncio | Silver item_details | sim | Warehouse |
| category_id | string | Categoria do anuncio | Silver item_details | sim | Warehouse |
| seller_id | string | Seller do anuncio | Silver item_details | sim | Warehouse |
| condition | string | Condicao do item | Silver item_details | sim | Warehouse |
| listing_type_id | string | Tipo de anuncio | Silver item_details | sim | Warehouse |
| permalink | string | URL publica do anuncio | Silver item_details | sim | Warehouse |

## Warehouse fact_seller_item_snapshot

| Coluna | Tipo | Descricao | Origem | Nullable | Camada |
|---|---|---|---|---|---|
| item_id | string | ID do anuncio | Silver item_details | nao | Warehouse |
| snapshot_date_key | integer | Chave da data do snapshot | derivado de ingested_at | nao | Warehouse |
| price | float | Preco do anuncio no snapshot | Silver item_details | sim | Warehouse |
| available_quantity | integer | Estoque disponivel no snapshot | Silver item_details | sim | Warehouse |
| sold_quantity | integer | Quantidade vendida no snapshot | Silver item_details | sim | Warehouse |
| status | string | Status do anuncio no snapshot | Silver item_details | sim | Warehouse |

## ML category_scores

| Coluna | Tipo | Descricao | Origem | Nullable | Camada |
|---|---|---|---|---|---|
| anomaly_score | float | Score de anomalia | ML | nao | Gold/ML |
| is_anomaly | boolean | Flag de anomalia | ML | nao | Gold/ML |
| opportunity_score | float | Marketplace Opportunity Score | ML | nao | Gold/ML |
| opportunity_rank | integer | Ranking por oportunidade | ML | nao | Gold/ML |

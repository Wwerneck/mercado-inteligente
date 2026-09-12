# Modelo Dimensional

## dim_category

Grain: uma linha por categoria do Mercado Livre monitorada.

Chave primaria: `category_id`.

## dim_domain

Grain: uma linha por combinacao dominio + categoria retornada pelo endpoint de descoberta.

Chave primaria: `domain_category_id`.

Relacionamento: `category_id` referencia `dim_category.category_id`.

## dim_date

Grain: uma linha por data de snapshot.

Chave primaria: `date_key` no formato `YYYYMMDD`.

## dim_seller

Grain: uma linha por seller autenticado monitorado.

Chave primaria: `seller_id`.

## dim_item

Grain: uma linha por anuncio autenticado monitorado.

Chave primaria: `item_id`.

Relacionamentos:

- `seller_id` referencia `dim_seller.seller_id`;
- `category_id` referencia categorias quando disponivel.

## fact_category_snapshot

Grain: uma linha por categoria por data de snapshot.

Chaves: `category_id`, `snapshot_date_key`.

Metricas atuais:

- quantidade de dominios associados;
- total de itens informado pela categoria;
- quantidade de subcategorias;
- profundidade na arvore de categorias;
- score de cobertura de catalogo.

## fact_marketplace_overview

Grain: uma linha por data de snapshot do marketplace monitorado.

Chave: `snapshot_date_key`.

Metricas atuais:

- total de categorias;
- total de dominios;
- total de itens nas categorias;
- media de subcategorias;
- ultima data de ingestao.

## fact_seller_item_snapshot

Grain: uma linha por anuncio por data de snapshot.

Chaves: `item_id`, `snapshot_date_key`.

Metricas atuais:

- preco;
- estoque disponivel;
- quantidade vendida;
- status do anuncio.

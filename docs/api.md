# API

A Fase 8 adiciona uma API REST com FastAPI.

## Executar

```bash
uvicorn src.api.main:app --reload
```

## Endpoints

- `GET /health`
- `GET /analytics/overview`
- `GET /analytics/categories`
- `GET /analytics/categories/{category_id}`
- `GET /analytics/seller-items`
- `GET /analytics/items`
- `GET /analytics/price-history`
- `GET /ml/opportunity-score`
- `GET /ml/anomalies`
- `GET /ml/metadata`
- `GET /ml/advanced-metadata`
- `GET /auth/meli/authorize`
- `POST /auth/meli/callback`
- `POST /auth/meli/refresh`
- `GET /auth/meli/status`
- `GET /pipeline/runs`
- `GET /pipeline/runs/latest`
- `GET /pipeline/observability`
- `GET /pipeline/runs/{run_id}`

Os dados de analytics sao lidos dos marts dbt no DuckDB. Os endpoints `GET /analytics/seller-items` e `GET /analytics/items` usam marts dbt quando existem e fallback para Parquet local quando necessario. Artefatos de ML continuam em `data/gold`.

## Pipeline

Os endpoints de pipeline leem manifestos em `data/pipeline_runs`:

- `GET /pipeline/runs`: lista execucoes recentes com status, duracao e resumo das tasks.
- `GET /pipeline/runs/latest`: retorna o manifesto completo mais recente.
- `GET /pipeline/runs/{run_id}`: retorna o manifesto completo de uma execucao especifica.

## OAuth Mercado Livre Opcional

O dashboard principal usa dados publicos de marketplace e nao exige que a conta seja vendedora. OAuth existe apenas para o modulo opcional de dados proprietarios do vendedor, como anuncios da propria conta.

Configure as credenciais no `.env`:

```bash
MELI_CLIENT_ID=seu_app_id
MELI_CLIENT_SECRET=sua_secret_key
MELI_REDIRECT_URI=http://localhost:8000/auth/meli/callback
MELI_USE_PKCE=false
MELI_TOKEN_STORE_PATH=data/secrets/meli_oauth_token.json
MELI_TOKEN_ENCRYPTION_KEY=
MELI_ENABLE_AUTHENTICATED_COLLECTION=false
```

Fluxo local:

1. Chame `GET /auth/meli/authorize`.
2. Abra a `authorization_url` retornada e autorize a aplicacao.
3. Envie o `code`, o `state` recebido no redirect e o `expected_state` retornado no passo 1 para `POST /auth/meli/callback`.
4. Use `POST /auth/meli/refresh` com o `refresh_token` quando o access token expirar.
5. Verifique `GET /auth/meli/status` para confirmar a conexao sem expor tokens completos.

O endpoint `GET /auth/meli/authorize?use_pkce=true` retorna tambem `code_verifier` para aplicacoes Mercado Livre com PKCE habilitado. Tokens sao persistidos localmente no caminho `MELI_TOKEN_STORE_PATH`, que deve permanecer fora do Git. Para criptografar o arquivo, gere uma chave Fernet e configure `MELI_TOKEN_ENCRYPTION_KEY`; tokens antigos em JSON continuam legiveis quando a chave nao estiver ativa.

Para habilitar a coleta de seller, altere `MELI_ENABLE_AUTHENTICATED_COLLECTION=true` e rode:

```bash
python -m src.ingestion.run_authenticated_collection
```

Quando habilitada, ela valida o token salvo, renova automaticamente quando estiver expirado e grava:

- retorno de `/users/me` em `data/bronze/authenticated_user`;
- IDs de anuncios de `/users/{user_id}/items/search` em `data/bronze/seller_items`;
- detalhes dos anuncios de `/items?ids=...` em `data/bronze/item_details`.
- descricoes de anuncios em `data/bronze/item_descriptions`;
- snapshots de preco, estoque e vendas em `data/bronze/item_price_snapshots`.

A fase Silver/Gold materializa esses snapshots em `data/silver/item_price_snapshots.parquet` e `data/gold/price_history.parquet`, com variacoes de preco, estoque e vendas por anuncio.

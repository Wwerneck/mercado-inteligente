# Pipeline

Fluxo executavel atual:

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

Execucao local:

```bash
python -m src.orchestration.run_phase_4
```

`extract_marketplace_data` executa coleta publica em lote usando `MELI_PUBLIC_QUERIES`.
Exemplo:

```env
MELI_PUBLIC_QUERIES=notebook,celular,smart tv,geladeira,fone bluetooth,cadeira gamer
```

O pipeline grava manifestos em `data/pipeline_runs`.

Esses manifestos tambem ficam disponiveis pela API:

- `GET /pipeline/runs`
- `GET /pipeline/runs/latest`
- `GET /pipeline/runs/{run_id}`

## Coleta autenticada opcional

`extract_authenticated_marketplace_data` fica desligada por padrao. Para habilitar dados proprietarios de uma conta vendedora, configure:

```env
MELI_ENABLE_AUTHENTICATED_COLLECTION=true
```

- Com a flag desligada, a task retorna `status=skipped` e o pipeline continua.
- Sem token OAuth salvo, a task retorna `status=skipped` e o pipeline continua.
- Com token OAuth salvo e flag ligada, a task coleta `/users/me`, `/users/{user_id}/items/search` e `/items?ids=...` para Bronze.

O runner orquestrado equivalente e:

```bash
python -m src.orchestration.run_phase_4
```

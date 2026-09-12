# IA Generativa Controlada

A Fase 10 adiciona um assistente analitico com camada semantica controlada.

## Principio

O assistente nao consulta tabelas livremente. Perguntas sao classificadas em intents permitidas e respondidas a partir de fontes Gold/ML conhecidas.

## Intents atuais

- `top_opportunities`
- `anomalies`
- `category_variation`
- `marketplace_overview`
- `advanced_ml_status`

## API

```bash
POST /ai/ask
```

Payload:

```json
{
  "question": "Quais categorias possuem maior Opportunity Score?"
}
```

## Limites

Perguntas fora das intents permitidas retornam uma resposta de fallback. Forecasting e variacoes temporais continuam bloqueados enquanto nao houver historico real suficiente.


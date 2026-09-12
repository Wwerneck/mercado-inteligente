# Marketplace Opportunity Score

Escala: 0 a 100.

Componentes atuais:

- cobertura de catalogo;
- baixa densidade competitiva;
- profundidade de categoria;
- estabilidade, penalizando anomalias.

Pesos padrao:

```text
catalog_coverage = 0.35
low_competition_density = 0.30
category_depth = 0.15
stability = 0.20
```

Os pesos sao normalizados no codigo para permitir configuracao futura sem quebrar a escala.

Limitacao: o score atual usa dados reais disponiveis por categoria. Quando a coleta de produtos/precos estiver liberada, o score deve incorporar concorrencia, historico de preco e volatilidade por produto.


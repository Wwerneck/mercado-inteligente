# Qualidade de Dados

Validacoes atuais:

- colunas obrigatorias;
- valores nulos em identificadores e datas;
- unicidade de chaves;
- integridade referencial via dbt;
- score de cobertura entre 0 e 100;
- score de oportunidade entre 0 e 100.

Ferramentas:

- validacoes Python em `src/validation`;
- testes dbt;
- testes automatizados com pytest.


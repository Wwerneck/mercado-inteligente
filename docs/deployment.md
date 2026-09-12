# Deploy Local

## Docker Compose

```bash
docker compose up --build
```

Servicos:

- Postgres: `localhost:5432`
- FastAPI: `http://localhost:8000`
- Streamlit: `http://localhost:8501`
- Airflow: `http://localhost:8080`

## Airflow

O Compose usa `docker/airflow.Dockerfile` para criar uma imagem baseada no Airflow oficial com as dependencias do projeto instaladas. O servico `airflow-init` executa a migracao do banco de metadados e cria o usuario local:

- usuario: `admin`
- senha: `admin`

Os containers do Airflow montam o repositorio em `/opt/airflow/project` e usam `PYTHONPATH=/opt/airflow/project`, permitindo importar os modulos em `src/` dentro da DAG.

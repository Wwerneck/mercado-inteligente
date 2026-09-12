from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    meli_base_url: str = Field(default="https://api.mercadolibre.com", alias="MELI_BASE_URL")
    meli_site_id: str = Field(default="MLB", alias="MELI_SITE_ID")
    meli_timeout_seconds: float = Field(default=20.0, alias="MELI_TIMEOUT_SECONDS")
    meli_max_retries: int = Field(default=3, alias="MELI_MAX_RETRIES")
    meli_rate_limit_seconds: float = Field(default=0.2, alias="MELI_RATE_LIMIT_SECONDS")
    meli_public_queries: str = Field(
        default="notebook,celular,smart tv,geladeira,fone bluetooth,cadeira gamer",
        alias="MELI_PUBLIC_QUERIES",
    )
    meli_auth_base_url: str = Field(
        default="https://auth.mercadolivre.com.br", alias="MELI_AUTH_BASE_URL"
    )
    meli_client_id: str | None = Field(default=None, alias="MELI_CLIENT_ID")
    meli_client_secret: str | None = Field(default=None, alias="MELI_CLIENT_SECRET")
    meli_redirect_uri: str | None = Field(default=None, alias="MELI_REDIRECT_URI")
    meli_use_pkce: bool = Field(default=False, alias="MELI_USE_PKCE")
    meli_token_store_path: Path = Field(
        default=Path("data/secrets/meli_oauth_token.json"), alias="MELI_TOKEN_STORE_PATH"
    )
    meli_token_encryption_key: str | None = Field(
        default=None, alias="MELI_TOKEN_ENCRYPTION_KEY"
    )
    meli_enable_authenticated_collection: bool = Field(
        default=False, alias="MELI_ENABLE_AUTHENTICATED_COLLECTION"
    )
    data_dir: Path = Field(default=Path("data"), alias="DATA_DIR")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    duckdb_path: Path = Field(
        default=Path("data/warehouse/mercado_intelligence.duckdb"), alias="DUCKDB_PATH"
    )
    postgres_dsn: str | None = Field(default=None, alias="POSTGRES_DSN")

    @property
    def public_queries(self) -> list[str]:
        return [query.strip() for query in self.meli_public_queries.split(",") if query.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

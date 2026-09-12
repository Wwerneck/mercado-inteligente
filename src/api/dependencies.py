from functools import lru_cache

from src.api.repository import AnalyticsRepository
from src.config.settings import get_settings


@lru_cache
def get_repository() -> AnalyticsRepository:
    settings = get_settings()
    return AnalyticsRepository(settings.duckdb_path, settings.data_dir)


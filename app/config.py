from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    hgbrasil_api_key: str
    hgbrasil_base_url: str = "https://api.hgbrasil.com/v2/finance/quotes"
    app_port: int = 8000
    app_host: str = "0.0.0.0"
    cache_ttl_seconds: int = 60
    redis_url: str = "redis://localhost:6379/0"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()

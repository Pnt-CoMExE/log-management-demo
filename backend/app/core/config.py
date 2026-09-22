from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_database_url(url: str) -> str:
    # Render/Heroku style postgres:// → SQLAlchemy + psycopg2
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Log Management Demo"
    secret_key: str = "change-me-in-production-use-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    database_url: str = "postgresql+psycopg2://logmgr:logmgr@localhost:5432/logmgr"

    retention_days: int = 7
    alert_webhook_url: str = ""
    cors_origins: str = "*"
    static_dir: str = ""  # if set, serve built frontend from this path

    # Seed users: password is "password" for both (demo only)
    admin_username: str = "admin"
    admin_password: str = "password"
    admin_tenant: str = "demoA"

    viewer_username: str = "viewer"
    viewer_password: str = "password"
    viewer_tenant: str = "demoA"

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_db(cls, v: object) -> object:
        if isinstance(v, str):
            return _normalize_database_url(v)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()

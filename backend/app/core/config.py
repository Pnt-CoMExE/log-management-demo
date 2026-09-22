from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Seed users: password is "password" for both (demo only)
    admin_username: str = "admin"
    admin_password: str = "password"
    admin_tenant: str = "demoA"

    viewer_username: str = "viewer"
    viewer_password: str = "password"
    viewer_tenant: str = "demoA"


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Application settings, loaded from environment variables and the project's .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

# config.py lives at backend/app/core/, so three levels up is the project root (copilot/).
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """All configuration the backend needs. Values come from .env or real environment variables."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # .env may hold settings for other parts of the project
    )

    app_env: str = "development"

    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379

    def database_url_for(self, database: str) -> URL:
        """Connection URL for any database on our server (used for the separate test database)."""
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=database,
        )

    @property
    def database_url(self) -> URL:
        """Connection URL for SQLAlchemy, built from the parts so special characters are escaped."""
        return self.database_url_for(self.postgres_db)


@lru_cache
def get_settings() -> Settings:
    """Load settings once and reuse them everywhere."""
    return Settings()

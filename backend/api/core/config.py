from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# api/ lives inside client2.0/
_CLIENT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_CLIENT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "EVA Agent API"
    api_prefix: str = "/v1"
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False

    jwt_secret: str = "dev-change-me-eva-jwt-secret-min-32b"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 6
    auth_session_expire_hours: int = 24 * 7
    mcp_credentials_key: str = ""

    cors_origins: str = "*"

    # ── Postgres ───────────────────────────────────────────────────────────
    pghost: str = "localhost"
    pgport: int = 5432
    pgdatabase: str = "eva"
    pguser: str = "postgres"
    pgpassword: str = "admin"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.pguser}:{self.pgpassword}"
            f"@{self.pghost}:{self.pgport}/{self.pgdatabase}"
        )

    data_root: Path = _CLIENT_ROOT / "data"
    client_root: Path = _CLIENT_ROOT

    execution_event_retention_days: int = 7
    execution_event_cleanup_interval_seconds: int = 3600
    max_parallel_bedrock: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()

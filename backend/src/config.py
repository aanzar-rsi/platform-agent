"""Agent environment and runtime configuration.

Loads `client2.0/.env` into the process environment and exposes typed settings
used across the agent, tools, and models packages.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# src/config.py → client2.0/
CLIENT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = CLIENT_ROOT / ".env"

# Populate os.environ so existing os.environ.get(...) call sites see .env values.
# Does not override variables already set in the process.
load_dotenv(ENV_FILE, override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Paths ──────────────────────────────────────────────────────────────
    client_root: Path = CLIENT_ROOT
    data_root: Path = CLIENT_ROOT / "data"
    logs_dir: Path = CLIENT_ROOT / "logs"

    # ── Postgres ───────────────────────────────────────────────────────────
    pghost: str = Field(default="localhost", validation_alias="PGHOST")
    pgport: int = Field(default=5432, validation_alias="PGPORT")
    pgdatabase: str = Field(default="eva", validation_alias="PGDATABASE")
    pguser: str = Field(default="postgres", validation_alias="PGUSER")
    pgpassword: str = Field(default="admin", validation_alias="PGPASSWORD")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.pguser}:{self.pgpassword}"
            f"@{self.pghost}:{self.pgport}/{self.pgdatabase}"
        )

    # ── LLM Gateway (LiteLLM / Foundry) ────────────────────────────────────
    # LLM_GATEWAY_API_KEY must be set in .env — never commit a real key.
    llm_gateway_url: str = Field(
        default="https://litellm-gateway.delightfulpebble-214bf13c.eastus2.azurecontainerapps.io/v1",
        validation_alias="LLM_GATEWAY_URL",
    )
    llm_gateway_api_key: str = Field(default="", validation_alias="LLM_GATEWAY_API_KEY")
    llm_model_id: str = Field(default="gpt-5-nano", validation_alias="LLM_MODEL_ID")

    # ── LLM call logging / mock replay ─────────────────────────────────────
    # Every call through src/models/llm_client.py is recorded to
    # logs/llm/{agent_id}.jsonl and the `llm_calls` Postgres table.
    llm_call_log_enabled: bool = Field(default=True, validation_alias="LLM_CALL_LOG_ENABLED")
    llm_call_log_to_db: bool = Field(default=True, validation_alias="LLM_CALL_LOG_TO_DB")
    # When on, an identical earlier call (same model + system prompt + prompt +
    # output_type + temperature) is replayed from `llm_calls` instead of hitting
    # the gateway. A cache miss falls through to a real call.
    mock_llm_call: bool = Field(
        default=False,
        validation_alias=AliasChoices("MOCK_LLM_CALL", "MOCK_LLM_CALL"),
    )

    # ── Embeddings (local) ─────────────────────────────────────────────────
    embed_method: str = Field(default="hf", validation_alias="EMBED_METHOD")  # "hf" | "numpy"
    embed_model_id: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        validation_alias="EMBED_MODEL_ID",
    )
    embed_dimensions: int = Field(default=384, validation_alias="EMBED_DIMENSIONS")

    # ── Tools ──────────────────────────────────────────────────────────────
    brave_search_api_key: str = Field(default="", validation_alias="BRAVE_SEARCH_API_KEY")

    # ── Agent behaviour ────────────────────────────────────────────────────
    agent_log_enabled: bool = Field(default=True, validation_alias="AGENT_LOG_ENABLED")
    max_loops: int = Field(default=500, validation_alias="MAX_LOOPS")

    # ── Experience / learner ───────────────────────────────────────────────
    experience_enabled: bool = Field(default=True, validation_alias="EXPERIENCE_ENABLED")
    experience_idle_seconds: int = Field(default=120, validation_alias="EXPERIENCE_IDLE_SECONDS")
    experience_poll_seconds: float = Field(default=20.0, validation_alias="EXPERIENCE_POLL_SECONDS")
    experience_top_k: int = Field(default=5, validation_alias="EXPERIENCE_TOP_K")

    # ── Process ────────────────────────────────────────────────────────────
    skip_venv_reexec: bool = Field(default=False, validation_alias="SKIP_VENV_REEXEC")

    def ensure_dirs(self) -> None:
        """Create standard data/log directories if missing.

        Users, chats, and checkpoints now live in Postgres — only the
        subsystems still on file storage need their directories.
        """
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.logs_dir / "llm").mkdir(parents=True, exist_ok=True)
        (self.data_root / "experience").mkdir(parents=True, exist_ok=True)
        (self.data_root / "analytics").mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings


# Eager singleton for convenient `from src.config import settings` imports.
settings = get_settings()

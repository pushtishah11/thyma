"""App settings, read from environment variables.

The defaults match docker-compose.yml, so local dev works without a .env file.
"""

import os
from dataclasses import dataclass

DEFAULT_DATABASE_URL = "postgresql+psycopg://thyma:thyma@localhost:5432/thyma"


@dataclass(frozen=True)
class Settings:
    database_url: str
    upload_dir: str
    llm_provider: str
    read_only_demo: bool


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes"}


def get_settings() -> Settings:
    return Settings(
        database_url=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
        upload_dir=os.environ.get("UPLOAD_DIR", "uploads"),
        llm_provider=os.environ.get("LLM_PROVIDER", "fake"),
        read_only_demo=_env_bool("READ_ONLY_DEMO", False),
    )

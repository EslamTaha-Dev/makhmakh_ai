from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR.parent / ".env"


class Settings(BaseSettings):
    app_name: str = "makhmakh Backend"
    app_version: str = "1.0.0"
    environment: str = "development"

    database_url: str

    redis_url: str = "redis://localhost:6379/0"
    run_jobs_inline: bool = False

    embedding_provider: Literal[
        "openai-compatible",
        "sentence-transformers",
    ] = "openai-compatible"
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = ""
    local_embedding_model: str = "intfloat/multilingual-e5-small"

    jwt_secret_key: str

    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    mock_ai: bool = False
    jwt_algorithm: str = "HS256"
    jwt_private_key: str | None = None
    jwt_public_key: str | None = None
    jwt_access_token_ttl_seconds: int = Field(default=900, ge=60, le=86400)

    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    frontend_url: str = "http://localhost:3000"
    mfa_encryption_key: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    ms_client_id: str = ""
    ms_client_secret: str = ""
    ms_tenant: str = "common"

    upload_dir: str = "uploads"

    upload_max_size_mb: int = Field(
        default=100,
        ge=1,
        le=2048,
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

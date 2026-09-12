from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    app_name: str = "Bosla Backend"
    app_version: str = "1.0.0"
    environment: str = "development"

    database_url: str

    redis_url: str = "redis://localhost:6379/0"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:1.5b"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    frontend_url: str = "http://localhost:3000"

    upload_dir: str = "uploads"

    upload_max_size_mb: int = Field(
        default=100,
        ge=1,
        le=2048,
    )

    payment_provider: str = "paymob"

    payment_request_timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=120,
    )

    payment_reconciliation_interval_seconds: int = Field(
        default=300,
        ge=30,
        le=3600,
    )

    subscription_duration_days: int = Field(
        default=30,
        ge=1,
        le=3650,
    )

    paymob_base_url: str = ""
    paymob_api_key: str = ""
    paymob_hmac_secret: str = ""
    paymob_checkout_url: str = ""

    fawry_base_url: str = ""
    fawry_merchant_code: str = ""
    fawry_security_key: str = ""

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
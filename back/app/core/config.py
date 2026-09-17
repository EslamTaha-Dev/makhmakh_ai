from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    app_name: str = "makhmakh Backend"
    app_version: str = "1.0.0"
    environment: str = "development"

    database_url: str

    redis_url: str = "redis://localhost:6379/0"
    arq_redis_url: str = "redis://localhost:6379/2"
    run_jobs_inline: bool = False

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:1.5b"
    active_embedding_model: str = "intfloat/multilingual-e5-small"
    active_embedding_dimension: int = Field(default=384, ge=1, le=4096)

    jwt_secret_key: str

    gemini_api_keys: str = ""
    openrouter_api_key: str = ""
    mock_ai: bool = False
    ai_gateway_provider: str = "gemini"
    ai_gateway_cooldown_seconds: int = 60
    ai_gateway_max_retries: int = 4
    jwt_algorithm: str = "HS256"
    jwt_private_key: str | None = None
    jwt_public_key: str | None = None
    jwt_access_token_ttl_seconds: int = Field(default=900, ge=60, le=86400)

    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    frontend_url: str = "http://localhost:3000"
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@localhost"
    smtp_starttls: bool = True
    email_verification_url: str = "http://localhost:3000/verify-email"
    password_reset_url: str = "http://localhost:3000/reset-password"
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
    paymob_public_key: str = ""
    paymob_integration_id: int | None = None
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

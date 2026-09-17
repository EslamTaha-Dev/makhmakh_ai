"""AI gateway: single entry point for every LLM call in the backend.

Provider credentials come from environment variables only. Gemini keys may be
supplied either as a comma-separated list or through the individual variables the
SRS documents (``GEMINI_API_KEY_DEV``, ``GEMINI_API_KEY_PROD_1``, ...), so the same
code works for local development and for the multi-project key rotation described
in ``01-ai-gateway-api-keys.md``.
"""

import logging
import os
import re

import httpx
from google import genai

from app.core.config import get_settings

from .key_pool import KeyPool, NoAvailableKeysError
from .task_router import get_model_for_task


logger = logging.getLogger("makhmakh.ai_gateway")


GEMINI_PROVIDER = "gemini"
OPENROUTER_PROVIDER = "openrouter"

GEMINI_LIST_ENV_VARS = (
    "GEMINI_API_KEYS",
    "GEMINI_API_KEY",
    "GEMINI_API_KEYS_POOL",
)

GEMINI_SINGLE_ENV_VARS = (
    "GEMINI_API_KEY_DEV",
    "GEMINI_API_KEY_PRIMARY",
    "GEMINI_API_KEY_BACKUP",
)

GEMINI_INDEXED_ENV_VAR = re.compile(
    r"^GEMINI_API_KEY_(?:PROD_)?\d+$"
)

OPENROUTER_ENV_VARS = (
    "OPENROUTER_API_KEYS",
    "OPENROUTER_API_KEY",
)

OPENROUTER_MODEL_ENV_VAR = "OPENROUTER_MODEL"
DEFAULT_OPENROUTER_MODEL = "google/gemini-2.5-flash"

AUTH_ERROR_MARKERS = (
    "401",
    "403",
    "api key not valid",
    "api_key_invalid",
    "unauthenticated",
    "permission_denied",
    "permission denied",
)

QUOTA_ERROR_MARKERS = (
    "429",
    "resource_exhausted",
    "resource exhausted",
    "quota",
    "rate limit",
    "overloaded",
)


class AIGatewayError(RuntimeError):
    """Base class for AI gateway failures."""


class AIGatewayUnavailable(AIGatewayError):
    """Raised when no usable provider credential is configured."""


class AIGatewayFailed(AIGatewayError):
    """Raised when every usable credential failed for a non-auth reason."""


def _split_keys(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []

    return [
        part.strip()
        for part in raw_value.replace(";", ",").split(",")
        if part.strip()
    ]


def _collect_gemini_keys() -> list[str]:
    keys: list[str] = []

    for env_var in GEMINI_LIST_ENV_VARS + GEMINI_SINGLE_ENV_VARS:
        keys.extend(_split_keys(os.getenv(env_var)))

    indexed_names = sorted(
        name
        for name in os.environ
        if GEMINI_INDEXED_ENV_VAR.match(name)
    )

    for env_var in indexed_names:
        keys.extend(_split_keys(os.getenv(env_var)))

    return keys


def _collect_openrouter_keys() -> list[str]:
    keys: list[str] = []

    for env_var in OPENROUTER_ENV_VARS:
        keys.extend(_split_keys(os.getenv(env_var)))

    return keys


def build_key_pool() -> KeyPool:
    """Build the key pool from the environment.

    Falls back to the ``gemini_api_keys`` / ``openrouter_api_key`` settings so the
    values can also be supplied through a ``.env`` file.
    """

    settings = get_settings()

    pool = KeyPool(
        cooldown_seconds=settings.ai_gateway_cooldown_seconds,
    )

    gemini_keys = _collect_gemini_keys()
    gemini_keys.extend(_split_keys(settings.gemini_api_keys))

    openrouter_keys = _collect_openrouter_keys()
    openrouter_keys.extend(_split_keys(settings.openrouter_api_key))

    pool.add_keys(
        [(key, GEMINI_PROVIDER) for key in gemini_keys]
    )

    pool.add_keys(
        [(key, OPENROUTER_PROVIDER) for key in openrouter_keys]
    )

    if len(pool) == 0:
        logger.warning(
            "AI gateway started without any provider credentials. "
            "Set GEMINI_API_KEYS (or GEMINI_API_KEY_DEV / GEMINI_API_KEY_PROD_N) "
            "to enable AI features."
        )

    return pool


key_pool = build_key_pool()


def refresh_key_pool() -> KeyPool:
    """Rebuild the pool from the environment (useful after rotating secrets)."""

    global key_pool

    key_pool = build_key_pool()

    return key_pool


def _call_gemini(model: str, prompt: str, api_key: str) -> str:
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    text = getattr(response, "text", None)

    if not text:
        raise AIGatewayFailed("Gemini returned an empty response.")

    return text


def _call_openrouter(model: str, prompt: str, api_key: str) -> str:
    base_url = os.getenv(
        "OPENROUTER_BASE_URL",
        "https://openrouter.ai/api/v1",
    )

    response = httpx.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": os.getenv(OPENROUTER_MODEL_ENV_VAR, DEFAULT_OPENROUTER_MODEL),
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60.0,
    )

    response.raise_for_status()

    payload = response.json()

    choices = payload.get("choices") or []

    if not choices:
        raise AIGatewayFailed("OpenRouter returned no choices.")

    content = (choices[0].get("message") or {}).get("content")

    if not content:
        raise AIGatewayFailed("OpenRouter returned an empty response.")

    return content


def _call_llm(
    provider: str,
    model: str,
    prompt: str,
    api_key: str,
) -> str:
    if provider == OPENROUTER_PROVIDER:
        return _call_openrouter(model, prompt, api_key)

    return _call_gemini(model, prompt, api_key)


def ai_gateway_execute(
    task_type: str,
    prompt: str,
    provider: str | None = None,
    max_retries: int | None = None,
) -> str:
    """Run a prompt through the configured provider with key rotation."""

    settings = get_settings()

    if settings.mock_ai:
        return f"[mock:{task_type}] This is a deterministic development response."

    target_provider = provider or settings.ai_gateway_provider
    model = get_model_for_task(task_type)

    attempts = max_retries or settings.ai_gateway_max_retries

    if not key_pool.has_provider(target_provider):
        raise AIGatewayUnavailable(
            f"No API key configured for AI provider '{target_provider}'."
        )

    last_error: Exception | None = None

    for _ in range(attempts):
        try:
            api_key = key_pool.reserve_key(target_provider=target_provider)
        except NoAvailableKeysError as exc:
            raise AIGatewayUnavailable(str(exc)) from exc

        try:
            return _call_llm(
                provider=target_provider,
                model=model,
                prompt=prompt,
                api_key=api_key,
            )

        except Exception as exc:  # noqa: BLE001 - provider errors are opaque
            message = str(exc).lower()

            if any(marker in message for marker in AUTH_ERROR_MARKERS):
                logger.warning(
                    "AI gateway disabled an invalid %s key.",
                    target_provider,
                )
                key_pool.disable_key(api_key)
                last_error = exc
                continue

            if any(marker in message for marker in QUOTA_ERROR_MARKERS):
                logger.warning(
                    "AI gateway parked a %s key after a quota error.",
                    target_provider,
                )
                key_pool.set_cooldown(api_key)
                last_error = exc
                continue

            raise AIGatewayFailed(str(exc)) from exc

    if last_error is not None:
        raise AIGatewayUnavailable(
            f"Every configured '{target_provider}' credential failed. "
            f"Last error: {last_error}"
        ) from last_error

    raise AIGatewayUnavailable(
        f"No usable '{target_provider}' credential available."
    )

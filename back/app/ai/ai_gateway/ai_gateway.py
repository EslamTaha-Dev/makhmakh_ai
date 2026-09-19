"""Single-credential gateway for backend AI requests."""

import logging
import os

import httpx
from google import genai

from app.core.config import get_settings

from .task_router import get_model_for_task


logger = logging.getLogger("makhmakh.ai_gateway")


GEMINI_PROVIDER = "gemini"
OPENROUTER_PROVIDER = "openrouter"

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
    """Raised when the configured provider cannot accept a request."""


class AIGatewayFailed(AIGatewayError):
    """Raised when a provider request fails for a non-auth reason."""


def get_provider_api_key(provider: str) -> str:
    """Return the single configured credential for a supported provider."""

    settings = get_settings()

    if provider == GEMINI_PROVIDER:
        api_key = settings.gemini_api_key
    elif provider == OPENROUTER_PROVIDER:
        api_key = settings.openrouter_api_key
    else:
        raise AIGatewayUnavailable(
            f"Unsupported AI provider '{provider}'."
        )

    api_key = api_key.strip()

    if not api_key:
        raise AIGatewayUnavailable(
            f"No API key configured for AI provider '{provider}'."
        )

    return api_key


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
) -> str:
    """Run one prompt using the configured provider's single API key."""

    settings = get_settings()

    if settings.mock_ai:
        return f"[mock:{task_type}] This is a deterministic development response."

    target_provider = provider or settings.ai_gateway_provider
    model = get_model_for_task(task_type)
    api_key = get_provider_api_key(target_provider)

    try:
        return _call_llm(
            provider=target_provider,
            model=model,
            prompt=prompt,
            api_key=api_key,
        )
    except AIGatewayError:
        raise
    except Exception as exc:  # noqa: BLE001 - provider errors are opaque
        message = str(exc).lower()

        if any(marker in message for marker in AUTH_ERROR_MARKERS):
            logger.warning(
                "The %s API credential was rejected.",
                target_provider,
            )
            raise AIGatewayUnavailable(
                f"The '{target_provider}' API credential was rejected."
            ) from exc

        if any(marker in message for marker in QUOTA_ERROR_MARKERS):
            logger.warning(
                "The %s provider rejected a request because of quota limits.",
                target_provider,
            )
            raise AIGatewayUnavailable(
                f"The '{target_provider}' provider quota is unavailable."
            ) from exc

        raise AIGatewayFailed(str(exc)) from exc

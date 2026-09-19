"""Vendor-neutral gateway for OpenAI-compatible text generation."""

import logging

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
)

from app.core.config import get_settings

logger = logging.getLogger("makhmakh.ai_gateway")

REQUEST_TIMEOUT_SECONDS = 60.0


class AIGatewayError(RuntimeError):
    """Base class for AI gateway failures."""


class AIGatewayUnavailable(AIGatewayError):
    """Raised when the configured provider cannot accept a request."""


class AIGatewayFailed(AIGatewayError):
    """Raised when a provider request fails for a non-auth reason."""


def create_openai_client(base_url: str, api_key: str) -> OpenAI:
    """Create a single-attempt client for an OpenAI-compatible endpoint."""

    return OpenAI(
        base_url=base_url,
        api_key=api_key,
        max_retries=0,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


def _required(value: str, env_var: str) -> str:
    value = value.strip()

    if not value:
        raise AIGatewayUnavailable(f"{env_var} is not configured.")

    return value


def get_configured_llm_model() -> str:
    """Return the configured model name, including a stable mock identifier."""

    settings = get_settings()

    if settings.mock_ai and not settings.llm_model.strip():
        return "mock"

    return _required(settings.llm_model, "LLM_MODEL")


def _call_llm(base_url: str, api_key: str, model: str, prompt: str) -> str:
    client = create_openai_client(base_url, api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    if not response.choices:
        raise AIGatewayFailed("The AI endpoint returned no choices.")

    content = response.choices[0].message.content

    if not isinstance(content, str) or not content.strip():
        raise AIGatewayFailed("The AI endpoint returned an empty response.")

    return content


def ai_gateway_execute(
    task_type: str,
    prompt: str,
) -> str:
    """Run one prompt through the configured OpenAI-compatible endpoint."""

    settings = get_settings()

    if settings.mock_ai:
        return f"[mock:{task_type}] This is a deterministic development response."

    base_url = _required(settings.llm_base_url, "LLM_BASE_URL")
    api_key = _required(settings.llm_api_key, "LLM_API_KEY")
    model = get_configured_llm_model()

    try:
        return _call_llm(
            base_url=base_url,
            api_key=api_key,
            model=model,
            prompt=prompt,
        )
    except AIGatewayError:
        raise
    except (AuthenticationError, PermissionDeniedError) as exc:
        logger.warning("The configured LLM credential was rejected.")
        raise AIGatewayUnavailable(
            "The configured LLM credential was rejected."
        ) from exc
    except RateLimitError as exc:
        logger.warning("The configured LLM endpoint is rate limited.")
        raise AIGatewayUnavailable(
            "The configured LLM endpoint is rate limited."
        ) from exc
    except (APIConnectionError, APITimeoutError) as exc:
        logger.warning("The configured LLM endpoint is unreachable.")
        raise AIGatewayUnavailable(
            "The configured LLM endpoint is unreachable."
        ) from exc
    except APIStatusError as exc:
        raise AIGatewayFailed(
            f"The LLM endpoint returned HTTP {exc.status_code}."
        ) from exc
    except Exception as exc:  # noqa: BLE001 - compatible gateways can vary
        raise AIGatewayFailed(str(exc)) from exc

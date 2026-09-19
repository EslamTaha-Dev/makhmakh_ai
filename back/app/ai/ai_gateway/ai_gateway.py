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

    error_code = "AI_PROVIDER_ERROR"
    http_status_code = 502

    def __init__(self, message: str, *, error_code: str | None = None):
        super().__init__(message)
        self.error_code = error_code or self.error_code


class AIGatewayUnavailable(AIGatewayError):
    """Raised when the configured provider cannot accept a request."""

    error_code = "AI_PROVIDER_UNAVAILABLE"
    http_status_code = 503


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
        raise AIGatewayUnavailable(
            f"{env_var} is not configured.",
            error_code="AI_NOT_CONFIGURED",
        )

    return value


def _provider_error_message(error: APIStatusError) -> str:
    """Extract a bounded provider message without logging response metadata."""

    body = getattr(error, "body", None)
    if not isinstance(body, dict):
        return "No provider error message."

    provider_error = body.get("error")
    if not isinstance(provider_error, dict):
        return "No provider error message."

    message = provider_error.get("message")
    if not isinstance(message, str) or not message.strip():
        return "No provider error message."

    return message.strip()[:1000]


def get_configured_llm_model() -> str:
    """Return the model configured for the OpenAI-compatible endpoint."""

    return _required(get_settings().llm_model, "LLM_MODEL")


def _call_llm(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    max_tokens: int,
) -> str:
    client = create_openai_client(base_url, api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
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

    base_url = _required(settings.llm_base_url, "LLM_BASE_URL")
    api_key = _required(settings.llm_api_key, "LLM_API_KEY")
    model = get_configured_llm_model()

    try:
        return _call_llm(
            base_url=base_url,
            api_key=api_key,
            model=model,
            prompt=prompt,
            max_tokens=settings.llm_max_tokens,
        )
    except AIGatewayError:
        raise
    except (AuthenticationError, PermissionDeniedError) as exc:
        logger.warning("The configured LLM credential was rejected.")
        raise AIGatewayUnavailable(
            "The configured LLM credential was rejected.",
            error_code="AI_CREDENTIAL_REJECTED",
        ) from exc
    except RateLimitError as exc:
        logger.warning("The configured LLM endpoint is rate limited.")
        raise AIGatewayUnavailable(
            "The configured LLM endpoint is rate limited.",
            error_code="AI_RATE_LIMITED",
        ) from exc
    except (APIConnectionError, APITimeoutError) as exc:
        logger.warning("The configured LLM endpoint is unreachable.")
        raise AIGatewayUnavailable(
            "The configured LLM endpoint is unreachable.",
            error_code="AI_PROVIDER_UNREACHABLE",
        ) from exc
    except APIStatusError as exc:
        logger.warning(
            "The LLM endpoint returned HTTP %s: %s",
            exc.status_code,
            _provider_error_message(exc),
        )

        if exc.status_code == 402:
            raise AIGatewayUnavailable(
                "The AI provider account has insufficient credits for this request.",
                error_code="AI_PROVIDER_CREDITS",
            ) from exc

        raise AIGatewayFailed(
            f"The LLM endpoint returned HTTP {exc.status_code}.",
            error_code="AI_PROVIDER_ERROR",
        ) from exc
    except Exception as exc:  # noqa: BLE001 - compatible gateways can vary
        raise AIGatewayFailed(str(exc)) from exc

from types import SimpleNamespace

import pytest

from app.ai.ai_gateway import ai_gateway


def settings(**overrides):
    values = {
        "gemini_api_key": "gemini-token",
        "openrouter_api_key": "openrouter-token",
        "ai_gateway_provider": "gemini",
        "mock_ai": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_provider_uses_one_configured_token(monkeypatch):
    monkeypatch.setattr(ai_gateway, "get_settings", settings)

    assert ai_gateway.get_provider_api_key("gemini") == "gemini-token"
    assert ai_gateway.get_provider_api_key("openrouter") == "openrouter-token"


def test_missing_or_unknown_provider_token_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        ai_gateway,
        "get_settings",
        lambda: settings(gemini_api_key=""),
    )

    with pytest.raises(ai_gateway.AIGatewayUnavailable):
        ai_gateway.get_provider_api_key("gemini")

    with pytest.raises(ai_gateway.AIGatewayUnavailable):
        ai_gateway.get_provider_api_key("unsupported")


def test_execute_calls_provider_once_with_configured_token(monkeypatch):
    monkeypatch.setattr(ai_gateway, "get_settings", settings)
    calls = []

    def fake_call_llm(provider, model, prompt, api_key):  # noqa: ANN001
        calls.append((provider, model, prompt, api_key))
        return "answer"

    monkeypatch.setattr(ai_gateway, "_call_llm", fake_call_llm)

    result = ai_gateway.ai_gateway_execute("chat", "hello")

    assert result == "answer"
    assert len(calls) == 1
    assert calls[0][0] == "gemini"
    assert calls[0][2:] == ("hello", "gemini-token")


@pytest.mark.parametrize(
    "message",
    [
        "401 API key not valid",
        "429 RESOURCE_EXHAUSTED: quota exceeded",
    ],
)
def test_execute_maps_credential_and_quota_errors_to_unavailable(
    monkeypatch,
    message,
):
    monkeypatch.setattr(ai_gateway, "get_settings", settings)

    def fail_once(**kwargs):  # noqa: ANN003
        raise RuntimeError(message)

    monkeypatch.setattr(ai_gateway, "_call_llm", fail_once)

    with pytest.raises(ai_gateway.AIGatewayUnavailable):
        ai_gateway.ai_gateway_execute("chat", "hello")


def test_execute_surfaces_other_provider_failures(monkeypatch):
    monkeypatch.setattr(ai_gateway, "get_settings", settings)

    def fail_once(**kwargs):  # noqa: ANN003
        raise ValueError("prompt rejected by safety filter")

    monkeypatch.setattr(ai_gateway, "_call_llm", fail_once)

    with pytest.raises(ai_gateway.AIGatewayFailed):
        ai_gateway.ai_gateway_execute("chat", "hello")


def test_mock_mode_does_not_require_a_token(monkeypatch):
    monkeypatch.setattr(
        ai_gateway,
        "get_settings",
        lambda: settings(gemini_api_key="", mock_ai=True),
    )

    assert ai_gateway.ai_gateway_execute("chat", "hello").startswith("[mock:chat]")

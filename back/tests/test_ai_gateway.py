from types import SimpleNamespace

import pytest

from app.ai.ai_gateway import ai_gateway


def settings(**overrides):
    values = {
        "llm_base_url": "https://router.example/v1",
        "llm_api_key": "single-token",
        "llm_model": "provider/model",
        "mock_ai": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_client_uses_configured_endpoint_without_retries(monkeypatch):
    captured = {}

    def fake_openai(**kwargs):  # noqa: ANN003
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(ai_gateway, "OpenAI", fake_openai)

    client = ai_gateway.create_openai_client(
        "https://router.example/v1",
        "single-token",
    )

    assert client is not None
    assert captured == {
        "base_url": "https://router.example/v1",
        "api_key": "single-token",
        "max_retries": 0,
        "timeout": ai_gateway.REQUEST_TIMEOUT_SECONDS,
    }


def test_execute_calls_chat_completions_once(monkeypatch):
    monkeypatch.setattr(ai_gateway, "get_settings", settings)
    calls = []

    def fake_call_llm(base_url, api_key, model, prompt):  # noqa: ANN001
        calls.append((base_url, api_key, model, prompt))
        return "answer"

    monkeypatch.setattr(ai_gateway, "_call_llm", fake_call_llm)

    result = ai_gateway.ai_gateway_execute("chat", "hello")

    assert result == "answer"
    assert calls == [
        (
            "https://router.example/v1",
            "single-token",
            "provider/model",
            "hello",
        )
    ]


@pytest.mark.parametrize(
    ("setting_name", "env_var"),
    [
        ("llm_base_url", "LLM_BASE_URL"),
        ("llm_api_key", "LLM_API_KEY"),
        ("llm_model", "LLM_MODEL"),
    ],
)
def test_missing_configuration_is_unavailable(
    monkeypatch,
    setting_name,
    env_var,
):
    monkeypatch.setattr(
        ai_gateway,
        "get_settings",
        lambda: settings(**{setting_name: " "}),
    )

    with pytest.raises(ai_gateway.AIGatewayUnavailable, match=env_var):
        ai_gateway.ai_gateway_execute("chat", "hello")


def test_call_llm_uses_standard_chat_completion_shape(monkeypatch):
    captured = {}

    def create(**kwargs):  # noqa: ANN003
        captured.update(kwargs)
        message = SimpleNamespace(content="portable answer")
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create),
        )
    )
    monkeypatch.setattr(
        ai_gateway,
        "create_openai_client",
        lambda base_url, api_key: client,
    )

    result = ai_gateway._call_llm(
        "https://router.example/v1",
        "single-token",
        "provider/model",
        "hello",
    )

    assert result == "portable answer"
    assert captured == {
        "model": "provider/model",
        "messages": [{"role": "user", "content": "hello"}],
    }


@pytest.mark.parametrize("content", [None, "", "   "])
def test_empty_completion_is_a_gateway_failure(monkeypatch, content):
    message = SimpleNamespace(content=content)
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(  # noqa: ARG005
                    choices=[SimpleNamespace(message=message)]
                )
            )
        )
    )
    monkeypatch.setattr(
        ai_gateway,
        "create_openai_client",
        lambda base_url, api_key: client,
    )

    with pytest.raises(ai_gateway.AIGatewayFailed, match="empty response"):
        ai_gateway._call_llm("https://router.example/v1", "token", "model", "hi")


def test_authentication_error_is_unavailable(monkeypatch):
    class FakeAuthenticationError(Exception):
        pass

    monkeypatch.setattr(ai_gateway, "get_settings", settings)
    monkeypatch.setattr(
        ai_gateway,
        "AuthenticationError",
        FakeAuthenticationError,
    )
    monkeypatch.setattr(
        ai_gateway,
        "_call_llm",
        lambda **kwargs: (_ for _ in ()).throw(FakeAuthenticationError()),
    )

    with pytest.raises(ai_gateway.AIGatewayUnavailable, match="credential"):
        ai_gateway.ai_gateway_execute("chat", "hello")


def test_rate_limit_error_is_unavailable(monkeypatch):
    class FakeRateLimitError(Exception):
        pass

    monkeypatch.setattr(ai_gateway, "get_settings", settings)
    monkeypatch.setattr(ai_gateway, "RateLimitError", FakeRateLimitError)
    monkeypatch.setattr(
        ai_gateway,
        "_call_llm",
        lambda **kwargs: (_ for _ in ()).throw(FakeRateLimitError()),
    )

    with pytest.raises(ai_gateway.AIGatewayUnavailable, match="rate limited"):
        ai_gateway.ai_gateway_execute("chat", "hello")


def test_status_error_is_gateway_failure(monkeypatch):
    class FakeStatusError(Exception):
        status_code = 400

    monkeypatch.setattr(ai_gateway, "get_settings", settings)
    monkeypatch.setattr(ai_gateway, "APIStatusError", FakeStatusError)
    monkeypatch.setattr(
        ai_gateway,
        "_call_llm",
        lambda **kwargs: (_ for _ in ()).throw(FakeStatusError()),
    )

    with pytest.raises(ai_gateway.AIGatewayFailed, match="HTTP 400"):
        ai_gateway.ai_gateway_execute("chat", "hello")


def test_mock_mode_does_not_require_configuration(monkeypatch):
    monkeypatch.setattr(
        ai_gateway,
        "get_settings",
        lambda: settings(
            llm_base_url="",
            llm_api_key="",
            llm_model="",
            mock_ai=True,
        ),
    )

    assert ai_gateway.ai_gateway_execute("chat", "hello").startswith("[mock:chat]")
    assert ai_gateway.get_configured_llm_model() == "mock"

"""Tests for the AI gateway key pool and execution wrapper.

These tests never touch the network: provider calls are monkeypatched, so they can
run in CI without Gemini credentials while still covering the rotation rules that
keep the AI features alive when a key is invalid or out of quota.
"""

import pytest

from app.ai.ai_gateway import ai_gateway
from app.ai.ai_gateway.key_pool import (
    KeyPool,
    KeyState,
    NoAvailableKeysError,
)


# --------------------------------------------------------------------------- #
# KeyPool
# --------------------------------------------------------------------------- #


def test_add_keys_ignores_blanks_and_duplicates():
    pool = KeyPool()

    added = pool.add_keys(
        [
            ("key-a", "gemini"),
            ("  ", "gemini"),
            ("", "gemini"),
            ("key-a", "gemini"),
            ("key-b", "gemini"),
        ]
    )

    assert added == 2
    assert len(pool) == 2


def test_reserve_key_raises_without_configured_provider():
    pool = KeyPool()
    pool.add_keys([("or-key", "openrouter")])

    with pytest.raises(NoAvailableKeysError):
        pool.reserve_key(target_provider="gemini")

    assert pool.has_provider("openrouter") is True


def test_reserve_key_rotates_through_available_keys():
    pool = KeyPool()
    pool.add_keys([("key-a", "gemini"), ("key-b", "gemini")])

    first = pool.reserve_key()
    second = pool.reserve_key()
    third = pool.reserve_key()

    assert {first, second} == {"key-a", "key-b"}
    assert third == first


def test_disabled_keys_leave_the_rotation():
    pool = KeyPool()
    pool.add_keys([("key-a", "gemini"), ("key-b", "gemini")])

    pool.disable_key("key-a")

    assert pool.reserve_key() == "key-b"
    assert pool.stats()["gemini"] == {
        "total": 2,
        "active": 1,
        "cooldown": 0,
        "disabled": 1,
    }

    pool.disable_key("key-b")

    with pytest.raises(NoAvailableKeysError):
        pool.reserve_key()


def test_cooldown_parks_and_then_releases_a_key():
    pool = KeyPool(cooldown_seconds=60)
    pool.add_keys([("key-a", "gemini")])

    pool.set_cooldown("key-a")

    with pytest.raises(NoAvailableKeysError):
        pool.reserve_key()

    # Simulate the cooldown window passing.
    pool._entries["key-a"].cooldown_until -= 61

    assert pool.reserve_key() == "key-a"
    assert pool._entries["key-a"].state is KeyState.ACTIVE


def test_stats_groups_by_provider():
    pool = KeyPool()
    pool.add_keys(
        [
            ("gem-1", "gemini"),
            ("gem-2", "gemini"),
            ("or-1", "openrouter"),
        ]
    )

    stats = pool.stats()

    assert stats["gemini"]["total"] == 2
    assert stats["openrouter"]["total"] == 1


# --------------------------------------------------------------------------- #
# Environment parsing
# --------------------------------------------------------------------------- #


class _IsolatedSettings:
    """Stand-in for app settings so a developer's .env cannot leak into tests."""

    gemini_api_keys = ""
    openrouter_api_key = ""
    ai_gateway_provider = "gemini"
    ai_gateway_cooldown_seconds = 60
    ai_gateway_max_retries = 4


def _isolate_settings(monkeypatch):
    monkeypatch.setattr(ai_gateway, "get_settings", lambda: _IsolatedSettings())


@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, []),
        ("", []),
        ("a,b", ["a", "b"]),
        ("a; b ", ["a", "b"]),
        ("  only  ", ["only"]),
    ],
)
def test_split_keys(raw, expected):
    assert ai_gateway._split_keys(raw) == expected


def test_build_key_pool_reads_list_and_indexed_env_vars(monkeypatch):
    for name in (
        "GEMINI_API_KEYS",
        "GEMINI_API_KEY",
        "GEMINI_API_KEYS_POOL",
        "GEMINI_API_KEY_DEV",
        "GEMINI_API_KEY_PRIMARY",
        "GEMINI_API_KEY_BACKUP",
        "GEMINI_API_KEY_PROD_1",
        "GEMINI_API_KEY_PROD_2",
        "OPENROUTER_API_KEYS",
        "OPENROUTER_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    monkeypatch.setenv("GEMINI_API_KEYS", "gem-a,gem-b")
    monkeypatch.setenv("GEMINI_API_KEY_PROD_2", "gem-c")
    _isolate_settings(monkeypatch)

    pool = ai_gateway.build_key_pool()

    assert len(pool) == 3
    assert pool.has_provider("gemini") is True
    assert pool.has_provider("openrouter") is False


def test_build_key_pool_without_credentials_is_empty(monkeypatch):
    for name in list(ai_gateway.GEMINI_LIST_ENV_VARS) + list(
        ai_gateway.GEMINI_SINGLE_ENV_VARS
    ):
        monkeypatch.delenv(name, raising=False)

    monkeypatch.setenv("GEMINI_API_KEYS", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    _isolate_settings(monkeypatch)

    pool = ai_gateway.build_key_pool()

    assert len(pool) == 0


# --------------------------------------------------------------------------- #
# ai_gateway_execute
# --------------------------------------------------------------------------- #


def test_execute_raises_when_provider_has_no_keys(monkeypatch):
    empty_pool = KeyPool()
    monkeypatch.setattr(ai_gateway, "key_pool", empty_pool)

    with pytest.raises(ai_gateway.AIGatewayUnavailable):
        ai_gateway.ai_gateway_execute("chat", "hello", provider="gemini")


def test_execute_rotates_past_an_invalid_key(monkeypatch):
    pool = KeyPool()
    pool.add_keys([("bad-key", "gemini"), ("good-key", "gemini")])
    monkeypatch.setattr(ai_gateway, "key_pool", pool)

    calls: list[str] = []

    def fake_call_llm(provider, model, prompt, api_key):  # noqa: ANN001
        calls.append(api_key)

        if api_key == "bad-key":
            raise RuntimeError("API key not valid. Please pass a valid API key.")

        return "answer from the good key"

    monkeypatch.setattr(ai_gateway, "_call_llm", fake_call_llm)

    result = ai_gateway.ai_gateway_execute(
        "chat",
        "summarise the lecture",
        provider="gemini",
    )

    assert result == "answer from the good key"
    assert calls == ["bad-key", "good-key"]
    assert pool.stats()["gemini"]["disabled"] == 1


def test_execute_parks_a_key_that_hit_its_quota(monkeypatch):
    pool = KeyPool(cooldown_seconds=30)
    pool.add_keys([("quota-key", "gemini"), ("spare-key", "gemini")])
    monkeypatch.setattr(ai_gateway, "key_pool", pool)

    def fake_call_llm(provider, model, prompt, api_key):  # noqa: ANN001
        if api_key == "quota-key":
            raise RuntimeError("429 RESOURCE_EXHAUSTED: quota exceeded")

        return "ok"

    monkeypatch.setattr(ai_gateway, "_call_llm", fake_call_llm)

    assert ai_gateway.ai_gateway_execute("chat", "hi", provider="gemini") == "ok"
    assert pool.stats()["gemini"]["cooldown"] == 1
    assert pool.stats()["gemini"]["active"] == 1


def test_execute_surfaces_non_auth_failures(monkeypatch):
    pool = KeyPool()
    pool.add_keys([("only-key", "gemini")])
    monkeypatch.setattr(ai_gateway, "key_pool", pool)

    def fake_call_llm(provider, model, prompt, api_key):  # noqa: ANN001
        raise ValueError("prompt rejected by the safety filter")

    monkeypatch.setattr(ai_gateway, "_call_llm", fake_call_llm)

    with pytest.raises(ai_gateway.AIGatewayFailed):
        ai_gateway.ai_gateway_execute("chat", "hi", provider="gemini")

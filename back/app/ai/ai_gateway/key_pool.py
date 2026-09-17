"""API key pool for the AI gateway.

Keys are supplied through environment variables (see ``ai_gateway.build_key_pool``).
The pool rotates through the keys that are currently usable, parks a key that hit a
quota error on a cooldown window, and permanently disables keys the provider rejects
as invalid. It never fabricates keys: when no key is configured the caller gets a
``NoAvailableKeysError`` instead of a silently broken request.
"""

import time
from dataclasses import dataclass
from enum import Enum


class KeyState(str, Enum):
    ACTIVE = "active"
    COOLDOWN = "cooldown"
    DISABLED = "disabled"


class NoAvailableKeysError(RuntimeError):
    """Raised when the pool holds no usable key for the requested provider."""


@dataclass
class KeyEntry:
    key: str
    provider: str
    state: KeyState = KeyState.ACTIVE
    cooldown_until: float = 0.0


class KeyPool:
    """Round-robin key pool with cooldown and disable support."""

    def __init__(self, cooldown_seconds: int = 60) -> None:
        self.cooldown_seconds = cooldown_seconds
        self._entries: dict[str, KeyEntry] = {}
        self._cursor = 0

    def add_keys(self, keys_with_provider: list[tuple[str, str]]) -> int:
        """Register keys. Blank keys are ignored and duplicates are not re-added."""

        added = 0

        for key, provider in keys_with_provider:
            normalized = (key or "").strip()

            if not normalized or normalized in self._entries:
                continue

            self._entries[normalized] = KeyEntry(
                key=normalized,
                provider=provider,
            )

            added += 1

        return added

    def __len__(self) -> int:
        return len(self._entries)

    def providers(self) -> set[str]:
        return {entry.provider for entry in self._entries.values()}

    def has_provider(self, provider: str) -> bool:
        return any(
            entry.provider == provider
            for entry in self._entries.values()
        )

    def _release_expired_cooldowns(self, now: float) -> None:
        for entry in self._entries.values():
            if (
                entry.state is KeyState.COOLDOWN
                and now >= entry.cooldown_until
            ):
                entry.state = KeyState.ACTIVE

    def reserve_key(self, target_provider: str = "gemini") -> str:
        """Return the next usable key for the provider.

        Raises ``NoAvailableKeysError`` when the provider has no configured key or
        when every configured key is disabled or cooling down.
        """

        now = time.time()

        self._release_expired_cooldowns(now)

        candidates = [
            entry
            for entry in self._entries.values()
            if entry.provider == target_provider
            and entry.state is KeyState.ACTIVE
        ]

        if not candidates:
            if not self.has_provider(target_provider):
                raise NoAvailableKeysError(
                    f"No API key configured for provider '{target_provider}'."
                )

            raise NoAvailableKeysError(
                f"All '{target_provider}' API keys are disabled or cooling down."
            )

        candidates.sort(key=lambda entry: entry.key)

        entry = candidates[self._cursor % len(candidates)]
        self._cursor += 1

        return entry.key

    def disable_key(self, key: str) -> None:
        entry = self._entries.get(key)

        if entry is not None:
            entry.state = KeyState.DISABLED

    def set_cooldown(self, key: str) -> None:
        entry = self._entries.get(key)

        if entry is not None:
            entry.state = KeyState.COOLDOWN
            entry.cooldown_until = time.time() + self.cooldown_seconds

    def stats(self) -> dict[str, dict[str, int]]:
        """Non-sensitive snapshot of the pool, safe to log or expose internally."""

        snapshot: dict[str, dict[str, int]] = {}

        for entry in self._entries.values():
            provider_stats = snapshot.setdefault(
                entry.provider,
                {"total": 0, "active": 0, "cooldown": 0, "disabled": 0},
            )

            provider_stats["total"] += 1

            if entry.state is KeyState.ACTIVE:
                provider_stats["active"] += 1
            elif entry.state is KeyState.COOLDOWN:
                provider_stats["cooldown"] += 1
            else:
                provider_stats["disabled"] += 1

        return snapshot

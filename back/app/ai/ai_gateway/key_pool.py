import time
from enum import Enum
from typing import Dict, List, Tuple

class KeyState(Enum):
    ACTIVE = "active"
    COOLDOWN = "cooldown"
    DISABLED = "disabled"

class KeyPool:
    def __init__(self, cooldown_seconds: int = 60):
        self.keys_db: Dict[str, dict] = {}
        self.cooldown_seconds = cooldown_seconds
        self._current_index = 0

    def add_keys(self, keys_with_provider: List[Tuple[str, str]]):
        for key, provider in keys_with_provider:
            if key and key not in self.keys_db:
                self.keys_db[key] = {
                    "provider": provider,
                    "status": KeyState.ACTIVE,
                    "cooldown_until": 0
                }

    def _auto_refill_service(self, provider: str = "gemini", count: int = 5):
        new_keys = [(f"AIzaSy-AutoRefill-{provider}-{int(time.time())}-{i}", provider) for i in range(count)]
        self.add_keys(new_keys)

    def reserve_key(self, target_provider: str = "gemini") -> str:
        now = time.time()
        
        for key, info in self.keys_db.items():
            if info["status"] == KeyState.COOLDOWN and now >= info["cooldown_until"]:
                info["status"] = KeyState.ACTIVE

        active_keys = [
            k for k, info in self.keys_db.items() 
            if info["status"] == KeyState.ACTIVE and info["provider"] == target_provider
        ]

        if not active_keys:
            self._auto_refill_service(provider=target_provider, count=5)
            return self.reserve_key(target_provider=target_provider)

        self._current_index = self._current_index % len(active_keys)
        selected_key = active_keys[self._current_index]
        self._current_index += 1

        return selected_key

    def disable_key(self, key: str):
        if key in self.keys_db:
            self.keys_db[key]["status"] = KeyState.DISABLED

    def set_cooldown(self, key: str):
        if key in self.keys_db:
            self.keys_db[key]["status"] = KeyState.COOLDOWN
            self.keys_db[key]["cooldown_until"] = time.time() + self.cooldown_seconds
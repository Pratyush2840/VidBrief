from abc import ABC, abstractmethod
from typing import Any, Optional

from cachetools import TTLCache

from config import settings


class ResultCache(ABC):
    """Swappable cache interface. Implement this against Redis (or anything
    else) later without touching the API layer -- callers only use get/set."""

    @abstractmethod
    def get(self, key: str) -> Optional[dict[str, Any]]:
        ...

    @abstractmethod
    def set(self, key: str, value: dict[str, Any]) -> None:
        ...


class InMemoryResultCache(ResultCache):
    def __init__(self, max_size: int, ttl_seconds: int):
        self._store: TTLCache[str, dict[str, Any]] = TTLCache(
            maxsize=max_size, ttl=ttl_seconds
        )

    def get(self, key: str) -> Optional[dict[str, Any]]:
        return self._store.get(key)

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._store[key] = value


result_cache: ResultCache = InMemoryResultCache(
    max_size=settings.cache_max_size, ttl_seconds=settings.cache_ttl_seconds
)

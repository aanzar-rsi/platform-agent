"""Small in-process TTL caches for hot Postgres lookups.

Not a distributed cache — this is a per-process speedup (every authenticated
request re-verifies its user, so a bare Postgres round trip on each request
would be wasteful). Invalidate explicitly on writes.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from cachetools import TTLCache

T = TypeVar("T")

# uid -> user row
user_cache: TTLCache[str, dict[str, Any] | None] = TTLCache(maxsize=1024, ttl=30)
# uid -> preferences dict
preferences_cache: TTLCache[str, dict[str, Any]] = TTLCache(maxsize=1024, ttl=30)
# uid -> mcp server list
mcp_cache: TTLCache[str, list[dict[str, Any]]] = TTLCache(maxsize=1024, ttl=30)


def cache_get_or_set(cache: TTLCache, key: str, loader: Callable[[], T]) -> T:
    if key in cache:
        return cache[key]
    value = loader()
    cache[key] = value
    return value


def cache_invalidate(cache: TTLCache, key: str) -> None:
    cache.pop(key, None)

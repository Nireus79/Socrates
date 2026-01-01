"""Caching layer for Socrates API."""

from .redis_cache import (
    CACHE_TTL_PRESENCE,
    CACHE_TTL_PROJECT,
    CACHE_TTL_PROJECT_LIST,
    CACHE_TTL_SEARCH,
    CACHE_TTL_SESSION,
    CACHE_TTL_USER,
    InMemoryCache,
    RedisCache,
    cache_key_presence,
    cache_key_project,
    cache_key_project_list,
    cache_key_rate_limit,
    cache_key_search,
    cache_key_session,
    cache_key_user,
    get_cache,
)

__all__ = [
    "RedisCache",
    "InMemoryCache",
    "get_cache",
    "cache_key_user",
    "cache_key_project",
    "cache_key_project_list",
    "cache_key_search",
    "cache_key_session",
    "cache_key_rate_limit",
    "cache_key_presence",
    "CACHE_TTL_USER",
    "CACHE_TTL_PROJECT",
    "CACHE_TTL_PROJECT_LIST",
    "CACHE_TTL_SEARCH",
    "CACHE_TTL_SESSION",
    "CACHE_TTL_PRESENCE",
]

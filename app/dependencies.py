"""Shared FastAPI dependencies."""

from functools import lru_cache

from app.settings import Settings, get_settings


@lru_cache
def get_cached_settings() -> Settings:
    return get_settings()

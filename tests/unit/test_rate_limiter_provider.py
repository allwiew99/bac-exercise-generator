import pytest
from _pytest.monkeypatch import MonkeyPatch

from bac_generator.api.routes import exercises
from bac_generator.core.config import settings
from bac_generator.services.rate_limiter import (
    InMemoryRateLimiter,
    RedisRateLimiter,
)


def test_get_rate_limiter_selects_memory(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "rate_limiter_provider",
        "memory",
    )

    limiter = exercises.get_rate_limiter()

    assert isinstance(
        limiter,
        InMemoryRateLimiter,
    )


def test_get_rate_limiter_selects_redis(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "rate_limiter_provider",
        "redis",
    )
    monkeypatch.setattr(
        settings,
        "redis_host",
        "10.76.187.139",
    )
    monkeypatch.setattr(
        settings,
        "redis_port",
        6379,
    )

    monkeypatch.setattr(
        exercises,
        "redis_rate_limiter",
        None,
    )

    limiter = exercises.get_rate_limiter()

    assert isinstance(
        limiter,
        RedisRateLimiter,
    )


def test_redis_provider_requires_host(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "rate_limiter_provider",
        "redis",
    )
    monkeypatch.setattr(
        settings,
        "redis_host",
        "",
    )

    monkeypatch.setattr(
        exercises,
        "redis_rate_limiter",
        None,
    )

    with pytest.raises(
        ValueError,
        match="REDIS_HOST must be configured",
    ):
        exercises.get_rate_limiter()


def test_get_rate_limiter_rejects_unknown_provider(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "rate_limiter_provider",
        "invalid",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported rate limiter provider",
    ):
        exercises.get_rate_limiter()
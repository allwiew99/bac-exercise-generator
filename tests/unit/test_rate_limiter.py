
from _pytest.monkeypatch import MonkeyPatch

from bac_generator.services.rate_limiter import InMemoryRateLimiter


async def test_rate_limiter_allows_requests_below_limit() -> None:
    limiter = InMemoryRateLimiter()

    assert await limiter.check(
        key="generate:user-1",
        limit=3,
        window_seconds=60,
    )

    assert await limiter.check(
        key="generate:user-1",
        limit=3,
        window_seconds=60,
    )

    assert await limiter.check(
        key="generate:user-1",
        limit=3,
        window_seconds=60,
    )


async def test_rate_limiter_blocks_request_after_limit() -> None:
    limiter = InMemoryRateLimiter()

    for _ in range(3):
        allowed = await limiter.check(
            key="generate:user-1",
            limit=3,
            window_seconds=60,
        )

        assert allowed

    blocked = await limiter.check(
        key="generate:user-1",
        limit=3,
        window_seconds=60,
    )

    assert blocked is False


async def test_rate_limiter_uses_independent_keys() -> None:
    limiter = InMemoryRateLimiter()

    for _ in range(2):
        assert await limiter.check(
            key="generate:user-1",
            limit=2,
            window_seconds=60,
        )

    assert (
        await limiter.check(
            key="generate:user-1",
            limit=2,
            window_seconds=60,
        )
        is False
    )

    assert await limiter.check(
        key="generate:user-2",
        limit=2,
        window_seconds=60,
    )


async def test_rate_limiter_separates_generate_and_submission() -> None:
    limiter = InMemoryRateLimiter()

    assert await limiter.check(
        key="generate:user-1",
        limit=1,
        window_seconds=60,
    )

    assert (
        await limiter.check(
            key="generate:user-1",
            limit=1,
            window_seconds=60,
        )
        is False
    )

    assert await limiter.check(
        key="submission:user-1",
        limit=1,
        window_seconds=60,
    )


async def test_rate_limiter_allows_request_after_window_expires(
    monkeypatch: MonkeyPatch,
) -> None:
    limiter = InMemoryRateLimiter()

    current_time = 1000.0

    monkeypatch.setattr(
        "bac_generator.services.rate_limiter.time.monotonic",
        lambda: current_time,
    )

    assert await limiter.check(
        key="generate:user-1",
        limit=1,
        window_seconds=60,
    )

    assert (
        await limiter.check(
            key="generate:user-1",
            limit=1,
            window_seconds=60,
        )
        is False
    )

    current_time = 1061.0

    assert await limiter.check(
        key="generate:user-1",
        limit=1,
        window_seconds=60,
    )
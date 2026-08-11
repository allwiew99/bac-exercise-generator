import asyncio
import time
from collections import defaultdict, deque
from typing import Protocol

from redis.asyncio import Redis


class RateLimiterProtocol(Protocol):
    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> bool: ...


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(
            deque
        )
        self._lock = asyncio.Lock()

    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> bool:
        now = time.monotonic()
        window_start = now - window_seconds

        async with self._lock:
            requests = self._requests[key]

            while (
                requests
                and requests[0] <= window_start
            ):
                requests.popleft()

            if len(requests) >= limit:
                return False

            requests.append(now)

            return True


class RedisRateLimiter:
    def __init__(
        self,
        host: str,
        port: int = 6379,
        *,
        prefix: str = "rate-limit",
    ) -> None:
        self._redis = Redis(
            host=host,
            port=port,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )

        self._prefix = prefix

    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> bool:
        redis_key = f"{self._prefix}:{key}"

        async with self._redis.pipeline(
            transaction=True
        ) as pipeline:
            pipeline.incr(redis_key)

            pipeline.expire(
                redis_key,
                window_seconds,
                nx=True,
            )

            results = await pipeline.execute()

        request_count = int(results[0])

        return request_count <= limit
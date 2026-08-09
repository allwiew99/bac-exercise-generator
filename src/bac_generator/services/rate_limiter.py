import asyncio
import time
from collections import defaultdict, deque
from typing import Protocol


class RateLimiterProtocol(Protocol):
    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> bool: ...


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
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

            while requests and requests[0] <= window_start:
                requests.popleft()

            if len(requests) >= limit:
                return False

            requests.append(now)

            return True
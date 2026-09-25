import argparse
import json
import math
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return round(ordered[index], 2)


def summarize(
    latencies_ms: list[float],
    successes: int,
    failures: int,
    elapsed_seconds: float,
    concurrency: int,
) -> dict[str, int | float | None]:
    total = successes + failures
    return {
        "concurrency": concurrency,
        "requests": total,
        "successes": successes,
        "failures": failures,
        "error_rate": round(failures / total, 4) if total else 0.0,
        "rps": round(total / elapsed_seconds, 2) if elapsed_seconds > 0 else 0.0,
        "p50_ms": _percentile(latencies_ms, 0.50),
        "p95_ms": _percentile(latencies_ms, 0.95),
        "p99_ms": _percentile(latencies_ms, 0.99),
    }


def _local_request() -> tuple[bool, float]:
    from fastapi.testclient import TestClient

    from bac_generator.main import app

    started = time.perf_counter()
    with TestClient(app) as client:
        response = client.get("/health")
    return response.status_code == 200, (time.perf_counter() - started) * 1000


def _live_request(url: str, authorization: str | None) -> tuple[bool, float]:
    headers = {"Authorization": authorization} if authorization else {}
    request = urllib.request.Request(url, headers=headers)
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            success = 200 <= response.status < 400
    except (urllib.error.URLError, TimeoutError):
        success = False
    return success, (time.perf_counter() - started) * 1000


def run_level(
    *,
    mode: str,
    concurrency: int,
    requests: int,
    url: str | None,
    authorization: str | None,
) -> dict[str, int | float | None]:
    if mode == "live" and requests > 20:
        raise ValueError("Live mode is capped at 20 requests per level.")
    if mode == "live" and not url:
        raise ValueError("Live mode requires --url.")

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        if mode == "mocked":
            results = list(pool.map(lambda _index: _local_request(), range(requests)))
        else:
            results = list(
                pool.map(
                    lambda _index: _live_request(str(url), authorization),
                    range(requests),
                )
            )
    elapsed = time.perf_counter() - started
    latencies = [latency for _success, latency in results]
    successes = sum(success for success, _latency in results)
    return summarize(
        latencies,
        successes,
        requests - successes,
        elapsed,
        concurrency,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Controlled backend load test")
    parser.add_argument("--mode", choices=("mocked", "live"), default="mocked")
    parser.add_argument("--url")
    parser.add_argument("--authorization")
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--concurrency", type=int, nargs="+", default=[1, 5, 10, 20])
    args = parser.parse_args()

    reports: list[dict[str, Any]] = []
    for concurrency in args.concurrency:
        reports.append(
            run_level(
                mode=args.mode,
                concurrency=concurrency,
                requests=args.requests,
                url=args.url,
                authorization=args.authorization,
            )
        )
    print(json.dumps({"mode": args.mode, "results": reports}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

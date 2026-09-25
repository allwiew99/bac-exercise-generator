# Load Test Results

Measured 2026-09-25 from the local development host. The harness is `scripts/load_test.py`; each level made 20 requests. Percentiles use nearest-rank calculation. These are small diagnostic samples, not capacity guarantees.

## Mocked/local backend overhead

Target: in-process FastAPI `/health` through `TestClient`, current branch, Python 3.12. External AI, retrieval, database, Redis, and sandbox calls are not included.

| Concurrency | Requests | RPS | p50 ms | p95 ms | p99 ms | Error rate |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 20 | 27.26 | 1.44 | 1.68 | 34.70 | 0% |
| 5 | 20 | 778.52 | 6.06 | 7.56 | 8.03 | 0% |
| 10 | 20 | 782.92 | 11.58 | 13.81 | 15.77 | 0% |
| 20 | 20 | 745.29 | 22.36 | 25.65 | 26.12 | 0% |

The concurrency-1 RPS includes repeated `TestClient` startup overhead and is not directly comparable with a persistent server benchmark.

The harness also has a `generation` scenario that POSTs a representative request. In mocked mode it replaces authentication, rate limiting, and the generation service with deterministic in-process fakes while retaining FastAPI routing, validation, serialization, middleware, and exception handling. Its smoke verification completed 4/4 requests at concurrency 1 and 4/4 at concurrency 2 with zero errors; that tiny run verifies harness behavior and is not reported as capacity evidence.

## Live Cloud Run infrastructure probe

Target: deployed revision `bac-exercise-generator-00019-xn4`, public `/health`, from the local host. This is a live network/Cloud Run latency probe, not an authenticated generation load test; it incurs no Gemini calls.

| Concurrency | Requests | RPS | p50 ms | p95 ms | p99 ms | Error rate |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 20 | 1.18 | 253.54 | 2,166.89 | 10,245.01 | 5% |
| 5 | 20 | 18.95 | 255.21 | 274.96 | 279.20 | 0% |
| 10 | 20 | 37.75 | 251.54 | 279.53 | 279.61 | 0% |
| 20 | 20 | 1.96 | 294.84 | 10,192.53 | 10,193.28 | 15% |

The harness has a 10-second client timeout. Four requests timed out: one at concurrency 1 and three at concurrency 20. No server-side status was available for those failures. The small sample and public health path cannot isolate Cloud Run cold starts, local network effects, or application saturation.

## Reproduction

```bash
PYTHONPATH=src python scripts/load_test.py --mode mocked --requests 20 --concurrency 1 5 10 20
PYTHONPATH=src python scripts/load_test.py --mode mocked --scenario generation \
  --requests 20 --concurrency 1 5 10 20
PYTHONPATH=src python scripts/load_test.py --mode live \
  --url https://bac-exercise-generator-4fyrwgwvwa-ew.a.run.app/health \
  --requests 20 --concurrency 1 5 10 20
PYTHONPATH=src python scripts/load_test.py --mode live --scenario generation \
  --url https://bac-exercise-generator-4fyrwgwvwa-ew.a.run.app/exercises/generate \
  --authorization 'Bearer <DISPOSABLE_FIREBASE_TOKEN>' \
  --requests 5 --concurrency 1
```

Authenticated live generation load remains unmeasured because no disposable Firebase test token was available. The live mode caps each concurrency level at 20 requests to prevent accidental paid-provider load.

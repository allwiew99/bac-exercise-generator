# Production Readiness Evidence

Evidence snapshot: 2026-09-25. Status vocabulary is restricted to `VERIFIED LIVE`, `VERIFIED`, `PARTIAL`, `NOT IMPLEMENTED`, and `BLOCKED BY USER ACTION`.

| Area | Status | Evidence / verification result | Remaining limitation |
|---|---|---|---|
| Application architecture | VERIFIED | Route/service/repository/provider boundaries inspected; 224 non-DB tests currently pass | Some dependency construction remains route-module based rather than lifespan-managed |
| Authentication | VERIFIED | Firebase bearer validation has safe 401 tests and no raw verifier exception logging | Live authenticated probe needs a disposable Firebase token |
| Authorization | VERIFIED | Repository and API tests scope exercise/submission/solution access by user and return 404 across ownership boundaries | No formal external penetration test |
| Secrets | VERIFIED | `.env` files are ignored; tracked-file inventory contains only examples; `.dockerignore` excludes local secrets | GitHub-native secret scanning enablement not verified |
| Database | PARTIAL | Async sessions, user-scoped repositories, explicit rollback tests | Final fresh-DB rerun blocked because local Docker daemon became unavailable |
| Migrations | VERIFIED | All four Alembic migrations upgraded from an empty PostgreSQL 16 database earlier in this audit | Not rerun after Docker daemon loss; no downgrade guarantee |
| Redis | VERIFIED | Explicit 2 s connect/read timeout; provider selection tests | Live Redis outage was not induced |
| Rate limiting | VERIFIED | Distributed limits are 10/60 s generation and 30/60 s submission; 429 tests pass; Redis outage fails closed with safe 503 | Atomic fixed-window semantics, not sliding-window fairness |
| RAG ingestion | VERIFIED | 317-document corpus hash and deterministic ingestion artifacts remain unchanged | Source-PDF acquisition is outside CI |
| RAG retrieval | VERIFIED LIVE | Live Vertex/Pinecone 30-query run succeeded 30/30 on 2026-09-25 | Provider availability remains external |
| RAG evaluation | VERIFIED LIVE | Recall@5 1.0000, MRR@5 1.0000, nDCG@5 0.9946, Recall@8 1.0000; mean/p95 retrieval 826.4/1430.4 ms | Golden set has 30 queries and is not a complete domain proof |
| LLM generation | PARTIAL | Schema validation, bounded six-attempt flow, stable invalid-output error, 60 s transport timeout | Current branch is not deployed; live generation not rerun in this audit |
| Generation evaluation | PARTIAL | Versioned 30-case, 10-topic, three-difficulty dataset and loader tests | Dataset has not been executed safely because Docker/local DB and disposable auth were unavailable; no metrics fabricated |
| Validation | VERIFIED | Schema, topic/difficulty, test-count, novelty, compile, runtime, and output tests pass | Automated checks cannot prove full semantic correctness |
| Sandbox | PARTIAL | No-egress command contract, outer 20 s bound, per-test 2 s execution bound, compilation/timeout tests | Cloud Run sandbox isolation not re-exercised live |
| Failure handling | VERIFIED | Failure matrix plus deterministic auth, validation, rate-limit, Redis, RAG, sandbox, and rollback tests | Some provider-SDK transport errors are covered through abstractions, not real outages |
| Timeouts | VERIFIED | Gemini 60 s, embedding 15 s, Pinecone 10 s, Redis 2 s, sandbox 20 s, program 2 s | PostgreSQL statement timeout is not explicitly configured |
| Retries | PARTIAL | Six-attempt generation/repair ceiling; persistence is not retried | Transient and deterministic LLM failures share one repair budget; no backoff yet |
| Request correlation | VERIFIED | Valid inbound IDs preserved; malicious/oversized IDs replaced; response header and JSON logs tested | No cross-service trace backend |
| Structured logging | VERIFIED | Allowlisted JSON formatter and lifecycle/failure events tested | New JSON logs are not deployed or observed live |
| Monitoring | VERIFIED LIVE | Cloud Run platform metrics available; health endpoint probed; two alert policies created | No custom stage metrics/dashboard |
| Alerting | PARTIAL | Enabled policies: sustained 5xx and p95 latency >10 s for five minutes | Project has no notification channels, so alerts cannot notify a person |
| CI | PARTIAL | Existing last main run 31727584582 passed commit `125c6d1`; branch workflow now adds scripts lint, compile, Docker, and frontend gates | New workflow not yet observed in GitHub CI at this snapshot |
| CD | VERIFIED LIVE | Main commit `125c6d10de451b4f6514d5d7d90f352d86d543b6` deployed successfully | Current hardening branch is not deployed; frontend deployment is outside this workflow |
| Containerization | VERIFIED | Baseline Docker build succeeded; `.dockerignore` now excludes secrets/caches | Post-change Docker rebuild blocked by Docker daemon loss |
| Performance | PARTIAL | Local overhead and live health latency measured at concurrency 1/5/10/20 | No authenticated end-to-end generation latency sample |
| Load testing | PARTIAL | Reproducible capped harness plus real local/live `/health` measurements in `LOAD_TEST_RESULTS.md` | Four live client timeouts; generation load needs a disposable Firebase token |
| Cost awareness | PARTIAL | Timestamped model formulas and infrastructure drivers in `docs/COST_MODEL.md` | No measured average token counts or billing export access |
| Security | PARTIAL | Auth/ownership/CORS/safe-error tests, ignored secrets, Docker context exclusion; production npm audit reports zero vulnerabilities after Next.js 16.3.6 upgrade | No DAST, dependency scanning workflow, or live sandbox escape test |
| Documentation | VERIFIED | Failure matrix, cost model, load results, architecture, README, and this evidence ledger | Live evidence must be refreshed after deployment |
| Reproducibility | PARTIAL | Locked frontend dependencies, Python project metadata, deterministic corpus/eval datasets, commands documented | Python dependencies are range-based rather than fully locked |
| Production verification | VERIFIED LIVE | Backend revision and image digest re-queried; `/health` returned 200 with request ID; frontend revision/digest re-queried | Serving revisions predate this branch; `/ready` and JSON events are not live |

## Exact live state

- Backend revision: `bac-exercise-generator-00019-xn4`
- Backend source commit/tag: `125c6d10de451b4f6514d5d7d90f352d86d543b6`
- Backend image digest: `sha256:aaaa57a25b05fdc720ae0e61751807fe827ba7e689f5252ed520306879e39510`
- Frontend revision: `bac-exercise-generator-frontend-00001-t5d`
- Frontend image digest: `sha256:7d100dda3c8a207b21af2a7ee5526495fc9c912a1882a5a6b756b77acb6d08b1`
- Current hardening branch: `codex/production-readiness` (not deployed)

## Verification commands and results

```text
python -m compileall -q src scripts                         PASS (virtualenv Python)
ruff check src tests alembic scripts                       PASS
mypy src tests                                              PASS (132 source files)
pytest excluding Docker-dependent repository integration   PASS (224 tests)
earlier full pytest with isolated PostgreSQL 16             PASS (226 tests)
frontend npm test                                           PASS (57 tests)
frontend npm run lint                                       PASS
frontend npm run build (Next.js 16.3.6)                    PASS
npm audit --omit=dev                                        PASS (0 production vulnerabilities)
baseline Docker build                                       PASS, digest sha256:b69a42f9...
fresh alembic upgrade head (PostgreSQL 16)                 PASS earlier in audit
live retrieval evaluation                                   PASS, 30/30
```

## Evidence boundaries

The 226-test full run, fresh migration, and baseline Docker build occurred before the Docker daemon disappeared. After the latest documentation/CI changes, the 224 tests not requiring a real PostgreSQL instance, Ruff, mypy, frontend lint/tests/build, and production dependency audit were rerun. Those states are deliberately not conflated.

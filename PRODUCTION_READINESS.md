# Production Readiness Evidence

Evidence snapshot: 2026-09-25. Status vocabulary is restricted to `VERIFIED LIVE`, `VERIFIED`, `PARTIAL`, `NOT IMPLEMENTED`, and `BLOCKED BY USER ACTION`.

| Area | Status | Evidence / verification result | Remaining limitation |
|---|---|---|---|
| Application architecture | VERIFIED | Route/service/repository/provider boundaries inspected; final CI passed all 236 tests | Some dependency construction remains route-module based rather than lifespan-managed |
| Authentication | VERIFIED | Firebase bearer validation has safe 401 tests and no raw verifier exception logging | Live authenticated probe needs a disposable Firebase token |
| Authorization | VERIFIED | Repository tests verify cross-user lookups return no exercise, submission, or solution; API handlers pass the authenticated UID into those scoped lookups | Explicit API-level user-A/user-B fixtures and an external penetration test remain absent |
| Secrets | VERIFIED | `.env` files are ignored; tracked-file inventory contains only examples; `.dockerignore` excludes local secrets | GitHub-native secret scanning enablement not verified |
| Database | VERIFIED | Async sessions, user-scoped repositories, flush/refresh-before-commit ordering, rollback tests, and PostgreSQL integration tests passed in final CI | No production failover exercise |
| Migrations | VERIFIED | Final CI upgraded all four Alembic migrations from an empty PostgreSQL service | No downgrade guarantee |
| Redis | VERIFIED | Explicit 2 s connect/read timeout; provider selection tests | Live Redis outage was not induced |
| Rate limiting | VERIFIED | Distributed limits are 10/60 s generation and 30/60 s submission; 429 tests pass; Redis outage fails closed with safe 503 | Atomic fixed-window semantics, not sliding-window fairness |
| RAG ingestion | VERIFIED | 317-document corpus hash and deterministic ingestion artifacts remain unchanged | Source-PDF acquisition is outside CI |
| RAG retrieval | VERIFIED LIVE | Live Vertex/Pinecone 30-query run succeeded 30/30 on 2026-09-25 | Provider availability remains external |
| RAG evaluation | VERIFIED LIVE | Recall@5 1.0000, MRR@5 1.0000, nDCG@5 0.9946, Recall@8 1.0000; mean/p95 retrieval 826.4/1430.4 ms | Golden set has 30 queries and is not a complete domain proof |
| LLM generation | PARTIAL | Schema validation, bounded six-attempt flow, stable invalid-output/transport errors, 60 s transport timeout | Current branch is not deployed; live generation not rerun in this audit |
| Generation evaluation | PARTIAL | Versioned 30-case, 10-topic, three-difficulty dataset and loader tests | Dataset has not been executed safely because Docker/local DB and disposable auth were unavailable; no metrics fabricated |
| Validation | VERIFIED | Schema, topic/difficulty, test-count, novelty, compile, runtime, and output tests pass | Automated checks cannot prove full semantic correctness |
| Sandbox | PARTIAL | No-egress command contract, outer 20 s bound, per-test 2 s execution bound, compilation/timeout tests | Cloud Run sandbox isolation not re-exercised live |
| Failure handling | VERIFIED | Failure matrix plus deterministic auth, validation, Gemini transport, rate-limit, Redis, RAG, sandbox, and pre-commit rollback tests | Real provider outages were not induced |
| Timeouts | VERIFIED | Gemini 60 s, embedding 15 s, Pinecone 10 s, Redis 2 s, sandbox 20 s, program 2 s, readiness 3 s overall | PostgreSQL statement timeout outside readiness is not explicitly configured |
| Retries | PARTIAL | Six-attempt generation/repair ceiling; persistence is not retried | Transient and deterministic LLM failures share one repair budget; no backoff yet |
| Request correlation | VERIFIED | Valid inbound IDs preserved; malicious/oversized IDs replaced; even unhandled 500 responses carry the response header | No cross-service trace backend |
| Structured logging | VERIFIED | Allowlisted JSON formatter redacts unstructured messages; lifecycle/failure events and safe public errors are tested | New JSON logs are not deployed or observed live |
| Monitoring | VERIFIED LIVE | Cloud Run platform metrics available; health endpoint probed; two alert policies created | No custom stage metrics/dashboard |
| Alerting | PARTIAL | Enabled policies: sustained 5xx and p95 latency >10 s for five minutes | Project has no notification channels, so alerts cannot notify a person |
| CI | VERIFIED | Branch run `36117487414` passed migrations, Ruff, mypy, 236 backend tests, compileall, backend Docker build, frontend lint, 57 tests, and production build | GitHub warns that current action releases rely on its temporary Node 24 compatibility mode |
| CD | VERIFIED LIVE | Main commit `125c6d10de451b4f6514d5d7d90f352d86d543b6` deployed successfully | Current hardening branch is not deployed; frontend deployment is outside this workflow |
| Containerization | VERIFIED | Final branch Docker build succeeded in CI; `.dockerignore` excludes secrets/caches | Image is a CI-local tag and was not pushed to Artifact Registry |
| Performance | PARTIAL | Local overhead and live health latency measured at concurrency 1/5/10/20 | No authenticated end-to-end generation latency sample |
| Load testing | PARTIAL | Reproducible capped harness supports mocked and live POST generation; real local/live `/health` measurements are recorded in `LOAD_TEST_RESULTS.md` | Four live client timeouts; authenticated live generation needs a disposable Firebase token |
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
python -m compileall -q src scripts                         PASS locally and in CI
ruff check src tests alembic scripts                       PASS locally and in CI
mypy src tests                                              PASS (132 source files, local and CI)
pytest excluding Docker-dependent repository integration   PASS locally (230 tests)
full pytest with PostgreSQL service                         PASS in CI (236 tests)
frontend npm test                                           PASS in CI (57 tests)
frontend npm run lint                                       PASS in CI
frontend npm run build (Next.js 16.3.6)                    PASS in CI
npm audit --omit=dev                                        PASS (0 production vulnerabilities)
backend Docker build                                        PASS in final CI
fresh alembic upgrade head (PostgreSQL service)            PASS in final CI
live retrieval evaluation                                   PASS, 30/30
```

## Evidence boundaries

Final evidence is GitHub Actions run `36117487414` for commit `19d05af`: all backend and frontend gates passed, including a fresh PostgreSQL migration and backend image build. Local Docker remained unavailable, so the CI-built image was not assigned a registry digest or run locally. Those states are deliberately not conflated.

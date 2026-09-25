# Production Readiness Evidence

Evidence snapshot: 2026-09-25. Status vocabulary is restricted to `VERIFIED LIVE`, `VERIFIED`, `PARTIAL`, `NOT IMPLEMENTED`, and `BLOCKED BY USER ACTION`.

| Area | Status | Evidence / verification result | Remaining limitation |
|---|---|---|---|
| Application architecture | VERIFIED | Route/service/repository/provider boundaries inspected; final CI passed all 236 tests | Some dependency construction remains route-module based rather than lifespan-managed |
| Authentication | VERIFIED | Firebase bearer validation has safe 401 tests and no raw verifier exception logging | Live authenticated probe needs a disposable Firebase token |
| Authorization | VERIFIED | Repository tests verify cross-user lookups return no exercise, submission, or solution; API handlers pass the authenticated UID into those scoped lookups | Explicit API-level user-A/user-B fixtures and an external penetration test remain absent |
| Secrets | VERIFIED | `.env` files are ignored; tracked-file inventory contains only examples; `.dockerignore` excludes local secrets | GitHub-native secret scanning enablement not verified |
| Database | VERIFIED LIVE | Async transaction tests passed; serving revision `/ready` completed its live PostgreSQL query | No production failover exercise |
| Migrations | VERIFIED LIVE | Production executions `bac-db-migrate-lk9m5` and CD execution `bac-db-migrate-jj4lk` completed successfully | No downgrade guarantee |
| Redis | VERIFIED LIVE | Explicit 2 s connect/read timeout; serving revision `/ready` completed its configured Redis ping | Live Redis outage was not induced |
| Rate limiting | VERIFIED | Distributed limits are 10/60 s generation and 30/60 s submission; 429 tests pass; Redis outage fails closed with safe 503 | Atomic fixed-window semantics, not sliding-window fairness |
| RAG ingestion | VERIFIED | 317-document corpus hash and deterministic ingestion artifacts remain unchanged | Source-PDF acquisition is outside CI |
| RAG retrieval | VERIFIED LIVE | Live Vertex/Pinecone 30-query run succeeded 30/30 on 2026-09-25 | Provider availability remains external |
| RAG evaluation | VERIFIED LIVE | Recall@5 1.0000, MRR@5 1.0000, nDCG@5 0.9946, Recall@8 1.0000; mean/p95 retrieval 826.4/1430.4 ms | Golden set has 30 queries and is not a complete domain proof |
| LLM generation | PARTIAL | Hardened generation code is deployed; schema validation, bounded six-attempt flow, stable errors, and 60 s transport timeout are tested | Authenticated live generation was not rerun because no disposable Firebase token was provided |
| Generation evaluation | PARTIAL | Versioned 30-case, 10-topic, three-difficulty dataset and loader tests | Dataset has not been executed safely because Docker/local DB and disposable auth were unavailable; no metrics fabricated |
| Validation | VERIFIED | Schema, topic/difficulty, test-count, novelty, compile, runtime, and output tests pass | Automated checks cannot prove full semantic correctness |
| Sandbox | PARTIAL | No-egress command contract, outer 20 s bound, per-test 2 s execution bound, compilation/timeout tests | Cloud Run sandbox isolation not re-exercised live |
| Failure handling | VERIFIED | Failure matrix plus deterministic auth, validation, Gemini transport, rate-limit, Redis, RAG, sandbox, and pre-commit rollback tests | Real provider outages were not induced |
| Timeouts | VERIFIED | Gemini 60 s, embedding 15 s, Pinecone 10 s, Redis 2 s, sandbox 20 s, program 2 s, readiness 3 s overall | PostgreSQL statement timeout outside readiness is not explicitly configured |
| Retries | PARTIAL | Six-attempt generation/repair ceiling; persistence is not retried | Transient and deterministic LLM failures share one repair budget; no backoff yet |
| Request correlation | VERIFIED | Valid inbound IDs preserved; malicious/oversized IDs replaced; even unhandled 500 responses carry the response header | No cross-service trace backend |
| Structured logging | VERIFIED LIVE | Serving revision emitted correlated `request_received` and `request_completed` JSON events for request `live-verify-ready-20260925` | No cross-service trace backend or custom stage metrics |
| Monitoring | VERIFIED LIVE | Cloud Run platform metrics available; health endpoint probed; two alert policies created | No custom stage metrics/dashboard |
| Alerting | PARTIAL | Enabled policies: sustained 5xx and p95 latency >10 s for five minutes | Project has no notification channels, so alerts cannot notify a person |
| CI | VERIFIED | Main run `36119292113` passed migrations, Ruff, mypy, 236 backend tests, compileall, backend Docker build, frontend lint, 57 tests, and production build | GitHub warns that current action releases rely on its temporary Node 24 compatibility mode |
| CD | VERIFIED LIVE | Run `36119292113` attempt 2 completed the production migration and Cloud Run deployment for main commit `d6b021d` | Frontend deployment is outside this workflow |
| Containerization | VERIFIED LIVE | Artifact Registry digest was deployed and independently read from revision `00020-5cm`; `.dockerignore` excludes secrets/caches | No signed-image or provenance policy |
| Performance | PARTIAL | Live `/ready`: c1 p50/p95 314.93/339.87 ms, c5 315.85/671.17 ms, c10 316.86/594.65 ms | At c20, 7/20 clients hit the 10 s timeout; no authenticated generation latency sample |
| Load testing | PARTIAL | Reproducible capped harness supports mocked and live POST generation; live readiness was measured at concurrency 1/5/10/20 | c20 readiness sample had 35% client timeouts; authenticated generation needs a disposable Firebase token |
| Cost awareness | PARTIAL | Timestamped model formulas and infrastructure drivers in `docs/COST_MODEL.md` | No measured average token counts or billing export access |
| Security | PARTIAL | Auth/ownership/CORS/safe-error tests, ignored secrets, Docker context exclusion; production npm audit reports zero vulnerabilities after Next.js 16.3.6 upgrade | No DAST, dependency scanning workflow, or live sandbox escape test |
| Documentation | VERIFIED LIVE | Failure matrix, cost model, load results, README, and this ledger now identify the serving revision and evidence boundaries | Must be refreshed after future deployments |
| Reproducibility | PARTIAL | Locked frontend dependencies, Python project metadata, deterministic corpus/eval datasets, commands documented | Python dependencies are range-based rather than fully locked |
| Production verification | VERIFIED LIVE | Revision/digest re-queried; `/health` and `/ready` returned 200; logs were observed; 82 post-rollout request records were all HTTP 200 and routed to the new revision | Authenticated generation and sandbox/persistence events await a disposable Firebase token |

## Exact live state

- Backend revision: `bac-exercise-generator-00020-5cm`
- Backend source commit/tag: `d6b021ddb77541f7520c93ec2fabe87c743bd1bd`
- Backend image digest: `sha256:c6b7ed18fce27e85b281e70fb1e942ca85908c00d48647cd493f55c72c03eb02`
- Frontend revision: `bac-exercise-generator-frontend-00001-t5d`
- Frontend image digest: `sha256:7d100dda3c8a207b21af2a7ee5526495fc9c912a1882a5a6b756b77acb6d08b1`
- Production traffic: 100% to `bac-exercise-generator-00020-5cm`
- Rollback revision retained: `bac-exercise-generator-00019-xn4` (`Ready=True`, zero traffic)
- Successful deployment migration execution: `bac-db-migrate-jj4lk`

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

GitHub Actions run `36119292113` attempt 2 deployed merge commit `d6b021d`. Independent Cloud Run inspection found revision `bac-exercise-generator-00020-5cm` ready with 100% traffic and the exact Artifact Registry digest above. `/ready` verifies PostgreSQL and Redis but deliberately does not call paid AI/retrieval providers. The former revision remains retained for rollback. Alert policies are enabled, but no notification channel exists, so alert delivery remains `PARTIAL` rather than `VERIFIED LIVE`.

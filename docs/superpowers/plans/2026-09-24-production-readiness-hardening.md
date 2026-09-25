# Production Readiness Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden and evidence the existing application for defensible small-production operation without changing its proven RAG architecture.

**Architecture:** Add configuration-backed boundary policies, allowlisted JSON telemetry, explicit readiness and rollback behavior, then deterministic failure/evaluation/load tooling. Preserve route/service/repository separation and Pinecone ranking.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy async, Redis, Gemini/Vertex, Pinecone, Firebase, Cloud Run sandbox, pytest, mypy, Ruff, Docker, Next.js.

**Spec:** `docs/superpowers/specs/2026-09-24-production-readiness-hardening-design.md`

## Global Constraints

- Do not replace Pinecone, add orchestration frameworks, or change retrieval ranking without benchmark evidence.
- Never log credentials, tokens, prompts, corpus content, hidden tests, reference solutions, or raw provider exceptions.
- Retry only bounded, transient, idempotent operations; never blindly retry persistence.
- `VERIFIED LIVE` requires direct evidence from the serving revision.
- Use only the repository `allwiew99/bac-exercise-generator`.

## Review Focus

- Malicious or oversized incoming request IDs must be replaced, not reflected into logs or headers.
- Provider exceptions containing sensitive text must map to stable safe events and responses.
- Redis loss must deterministically fail closed without silently using process-local limiting.
- Persistence failure after successful generation must roll back and return no exercise.
- User A must receive no existence or solution information about User B's exercise.

---

### Task 1: Correlation and structured request telemetry

**Files:** Modify `src/bac_generator/api/middleware.py`, `src/bac_generator/core/logging_config.py`, `src/bac_generator/api/exception_handlers.py`; test `tests/integration/test_request_id.py` and create `tests/unit/test_logging_config.py`.

**Interfaces:** Produces validated `X-Request-ID` values and `log_event(event, **fields)` with an explicit field allowlist.

- [ ] Add tests showing invalid request IDs are replaced and JSON records omit unknown/sensitive fields.
- [ ] Run focused tests and confirm they fail for the missing validation/JSON behavior.
- [ ] Implement minimal request-ID validation, JSON formatting, request lifecycle events, and safe exception events.
- [ ] Run focused tests, then the full backend suite.
- [ ] Commit `feat: add safe structured request observability`.

### Task 2: Explicit dependency policies and failure behavior

**Files:** Modify `core/config.py`, Gemini, Vertex, Pinecone, Redis, Firebase and sandbox boundary modules; extend their unit tests.

**Interfaces:** Produces validated timeout/retry settings and stable dependency exceptions/events. Redis remains fail-closed.

- [ ] Add failing tests for configured timeouts, transient retry bounds, Gemini 429/timeout/malformed output, Vertex/Pinecone failure, Redis failure, Firebase failure, and sandbox compile/execution timeout.
- [ ] Confirm each new test fails for the intended missing behavior.
- [ ] Implement only the bounded timeout/retry and safe mapping needed by the tests.
- [ ] Run focused tests and full backend suite.
- [ ] Commit `feat: harden external dependency boundaries`.

### Task 3: Persistence, readiness, and authorization

**Files:** Modify `db/session.py`, repositories, health route/dependencies, route exception mapping; extend integration repository/exercise/health tests.

**Interfaces:** Produces `/ready`, explicit rollback on write failure, and non-enumerating user-scoped access.

- [ ] Add failing tests for database/Redis readiness, rollback after insert failure, persistence failure after generation, and cross-user exercise/solution access.
- [ ] Confirm failures reflect missing behavior.
- [ ] Implement bounded readiness and rollback-safe repositories while preserving thin routes.
- [ ] Run focused tests, fresh-database `alembic upgrade head`, and full backend suite.
- [ ] Commit `feat: add readiness and transactional failure safety`.

### Task 4: Failure matrix and deterministic injection coverage

**Files:** Create `tests/integration/test_failure_modes.py`; create `docs/PRODUCTION_FAILURE_MODES.md`.

**Interfaces:** Documents status code, safe message, logging, side effects, idempotency, and local/live evidence for every required dependency failure.

- [ ] Add API-level tests for all 16 requested failure scenarios, reusing real services with only external boundaries replaced.
- [ ] Run tests and record any missing behavior as failing cases before fixes.
- [ ] Make the smallest service/handler changes needed, then verify no invalid persistence or unsafe partial state.
- [ ] Populate the evidence matrix from test names and observed live evidence only.
- [ ] Commit `test: add deterministic production failure scenarios`.

### Task 5: Generation evaluation and load tooling

**Files:** Create `data/evaluation/generation_cases.json`, `scripts/evaluate_generation.py`, `scripts/load_test.py`, unit tests, and `LOAD_TEST_RESULTS.md` only after measurements.

**Interfaces:** Evaluation emits JSON metrics with sample counts and never invents results; load tool supports `mocked` and capped `live` modes at concurrency 1/5/10/20.

- [ ] Add failing parser/aggregation tests for 30 representative cases and latency/success metrics.
- [ ] Implement the deterministic dataset loader, evaluator, and bounded load runner.
- [ ] Run unit tests, a local mocked load test, and live capped runs only if credentials and safe auth are available.
- [ ] Record environment, revision, sample count, percentiles, errors, and limitations from actual output.
- [ ] Commit `eval: add generation quality and controlled load benchmarks`.

### Task 6: CI, operations, security, and cost evidence

**Files:** Modify `.github/workflows/ci.yml`; create operations scripts and `docs/COST_MODEL.md`; update `.env.example`.

**Interfaces:** CI covers backend compile/static/tests/migrations/Docker and frontend lint/test/build; ops scripts are idempotent and do not embed secrets.

- [ ] Add executable checks for tracked-file secret scanning and CI workflow behavior where practical.
- [ ] Add missing frontend and Docker gates without replacing the existing deploy flow.
- [ ] Add idempotent monitoring/alert configuration for sustained 5xx and latency, and timestamped cost assumptions from primary pricing sources.
- [ ] Run local equivalents and inspect workflow syntax/diff.
- [ ] Commit `ops: strengthen ci monitoring and cost visibility`.

### Task 7: Production evidence and documentation

**Files:** Create `PRODUCTION_READINESS.md`; update `README.md` and production architecture docs.

**Interfaces:** Every checklist item uses only `VERIFIED LIVE`, `VERIFIED`, `PARTIAL`, `NOT IMPLEMENTED`, or `BLOCKED BY USER ACTION`.

- [ ] Re-run all local quality gates, fresh migrations, Docker build, retrieval evaluation, generation evaluation, and controlled load tests.
- [ ] Push the branch and inspect CI only when authorized by the user's Git instruction; do not merge without explicit authorization.
- [ ] If deployment occurs through the authorized main workflow, re-query backend/frontend revisions, image digests, health/readiness, logs, monitoring, and alert policies.
- [ ] Update documents so claims match direct evidence and record every remaining limitation.
- [ ] Commit `docs: record verified production readiness state`.

### Task 8: Whole-branch review and handoff

**Files:** All changed files.

**Interfaces:** Produces a reviewed branch with an evidence-backed final audit.

- [ ] Generate a whole-branch review package and review security, failure behavior, privacy, deployment safety, and the five Review Focus cases.
- [ ] Re-grade findings; fix Critical/Important items with red-green tests and defer only true minors.
- [ ] Run the complete verification matrix again and inspect `git diff --check` plus tracked-file secret scan.
- [ ] Use the branch-finishing workflow and report exact revisions, digests, results, limitations, and any required user action.

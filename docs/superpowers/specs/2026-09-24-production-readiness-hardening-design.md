# Production Readiness Hardening Design

## Intent

Bring the existing Bac Exercise Generator to a defensible small-production state without replacing its proven Pinecone RAG design or adding unrelated infrastructure. Evidence must distinguish implemented, locally verified, CI verified, configured, deployed, and live verified behavior.

## Current baseline

The backend is deployed from commit `125c6d10de451b4f6514d5d7d90f352d86d543b6` as Cloud Run revision `bac-exercise-generator-00019-xn4`, image digest `sha256:aaaa57a25b05fdc720ae0e61751807fe827ba7e689f5252ed520306879e39510`. The frontend is separately deployed as `bac-exercise-generator-frontend-00001-t5d`, image digest `sha256:7d100dda3c8a207b21af2a7ee5526495fc9c912a1882a5a6b756b77acb6d08b1`. Local baseline: 214 backend tests and 57 frontend tests pass; Ruff, mypy, frontend build, and Docker build pass. The live health endpoint returns 200 with an `X-Request-ID`. No Cloud Monitoring alert policies are currently visible.

## Design

### Boundary reliability

Every external boundary will expose an explicit timeout and a deliberate retry/failure policy through validated settings. Read-only transient provider calls may use bounded retries; database writes and other side effects will not be blindly retried. Redis rate limiting will fail closed because bypassing abuse controls during an outage can multiply paid AI work. RAG remains fail-open only because that is the current declared product policy; failures must be observable and generation must still pass all downstream validation.

### Request correlation and observability

Accept an incoming request ID only when it matches a conservative length/character allowlist; otherwise generate a UUID. Emit single-line JSON logs with an allowlisted schema. Middleware records `request_received` and `request_completed`; services add retrieval, generation, validation, sandbox, persistence, and rate-limit events. Logs must never contain tokens, prompts, retrieved text, hidden tests, solutions, or raw provider exception strings.

### Health semantics

Keep `/health` as process liveness. Add `/ready` as a bounded core-readiness probe that checks database and, when configured, Redis without calling Gemini, Vertex, Pinecone, or Firebase. This avoids paid traffic and provider-induced deployment flapping while still detecting critical stateful dependency loss.

### Persistence and authorization

Repository writes explicitly roll back on failure. Existing user-scoped queries remain the ownership boundary and gain broken-object-level authorization coverage. Generation must persist only after retrieval, generation, novelty, schema, compilation, and test validation succeed.

### Evaluation and operations

Preserve the 30-query retrieval benchmark and current ranking decision. Add a versioned 30-case generation evaluation dataset plus a runner that records only real measurements. Add a controlled mocked/local load harness and a capped live mode. Create failure-mode, load-test, cost, and production-readiness evidence documents. Monitoring policies are added only through an idempotent script; live creation and deployment are performed only when existing credentials and permissions permit.

## Security and privacy

Frontend Firebase web configuration is treated as browser-visible configuration, while server credentials remain in Secret Manager. Secret scans operate on tracked files. Error responses and logs use stable safe messages, never provider payloads. Sandbox output is bounded before surfacing to clients or logs.

## Verification

Each behavior change follows a red-green test cycle. Completion requires backend and frontend suites, static checks, fresh-database migrations, Docker build, tracked-file secret scan, retrieval evaluation where credentials permit, controlled generation/load measurements where credentials permit, CI evidence after push, and re-querying Cloud Run plus logs and monitoring after rollout.

## Explicit limitations

Local tests cannot prove Cloud Run sandbox isolation, provider behavior, CI, deployment, live observability, or alert delivery. Those remain `PARTIAL` or `BLOCKED BY USER ACTION` until directly observed. Automatic generation checks cannot prove full semantic correctness of Romanian informatics exercises.

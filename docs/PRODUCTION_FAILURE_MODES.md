# Production Failure Modes

Evidence recorded 2026-09-24. `Local` means an automated test ran against local code; it is not live-production proof. Provider payloads, prompts, tokens, retrieved content, hidden tests, and solutions are excluded from logs.

| Dependency | Failure mode | Current behavior | Desired behavior | Implementation | Test evidence | Live evidence |
|---|---|---|---|---|---|---|
| Gemini | Timeout | Mapped through the generation error contract; client has a 60 s request timeout | Bounded attempts, safe 502 after exhaustion, no persistence | `GeminiClient`, `ExerciseService` | PARTIAL: timeout configuration and generation exhaustion are unit tested; transport timeout classification is not yet isolated | None |
| Gemini | HTTP 429 | API status becomes `LLMResponseError`; generation attempts are bounded | Retry only within the six-attempt generation budget, then safe 502 | `GeminiClient`, `ExerciseService` | `test_gemini_api_failure_enters_existing_generation_retry_contract`, `test_generate_raises_after_max_attempts` | None |
| Gemini | Invalid structured output | Stable `LLMResponseError`; provider content omitted | Bounded repair attempt, safe 502 on exhaustion | `GeminiClient`, `ExerciseService` | `test_invalid_structured_output_does_not_leak_provider_content`, service retry tests | None |
| Vertex embeddings | Timeout/unavailable | 15 s client timeout; RAG provider applies configured fail-open/fail-closed policy | Safe observable fallback only when `RAG_FAIL_OPEN=true` | `VertexEmbeddingClient`, `RagContextProvider` | `test_vertex_client_configures_request_timeout`, RAG failure tests | None |
| Pinecone | Timeout/unavailable | 10 s client timeout; RAG provider applies configured policy | Preserve no-RAG fallback only when explicitly configured | `PineconeRepository`, `RagContextProvider` | Pinecone timeout configuration plus RAG initialization/retrieval failure tests | None |
| Retrieval | No useful results | Empty context proceeds to validated generation | Generate without context and never bypass novelty/schema/code checks | `RetrievalService`, `RagContextProvider`, `ExerciseService` | sparse/empty and fail-open unit coverage | None |
| Redis | Unavailable | Fails closed with safe 503; no in-memory production fallback | Deterministic fail-closed protection against paid-work amplification | `RedisRateLimiter`, exception handler | `test_generate_fails_closed_with_safe_503_when_redis_is_unavailable` | None |
| PostgreSQL | Unavailable/write failure | Write attempts roll back; readiness returns safe 503 | No partial row and no provider detail leakage | repositories, `/ready` | `test_exercise_create_rolls_back_when_commit_fails`, readiness tests | None |
| Firebase | Missing/invalid token or verifier failure | Safe 401 and allowlisted structured event | No raw token/provider exception in response or logs | `get_current_user` | `tests/unit/test_auth.py` | Unauthenticated live generation probe not yet recorded |
| Sandbox | Compilation timeout | Outer 20 s bound maps to safe validation failure | No persistence | `SandboxCodeRunner`, validators | timeout/compilation tests | None |
| Sandbox | Execution timeout/infinite loop | Each generated test has a 2 s subprocess bound inside sandbox | Terminate, reject candidate, no persistence | sandbox runner script | script contract and validator timeout tests; live isolation not proven locally | None |
| Generated C++ | Compilation failure | Candidate rejected with 422 after attempt budget | No invalid exercise persisted | `CodeValidator`, `ExerciseService` | code-validator and API validation tests | None |
| Generated solution | Test-case mismatch | Candidate rejected and repaired within bounded attempts | No invalid exercise persisted | `ExerciseValidator`, code runners | validation and generation retry tests | None |
| Persistence | Failure after successful generation | Transaction rollback; exception propagates as failure | No exercise response and no partial row | `ExerciseRepository` | rollback unit test; API mapping remains partial | None |
| Novelty guard | Exact/near copy | Rejects and enters bounded repair flow | No copied exercise persisted | `ExerciseNoveltyValidator`, `ExerciseService` | novelty threshold/copy/repair tests | None |
| Client request | Malformed schema | FastAPI/Pydantic returns 422 before generation | No provider calls or persistence | request schemas/routes | schema and integration tests | None |

## Retry and side-effect policy

- Retrieval and model generation are read-only external operations, but the total generation attempt count is bounded by `LLM_MAX_ATTEMPTS`.
- Invalid output and deterministic validation failures use the same bounded repair budget; they are never retried indefinitely.
- PostgreSQL writes are not automatically retried. A failed write is rolled back and propagated.
- Redis rate-limit decisions fail closed. Falling back to per-instance memory would make limits bypassable during an outage or scale-out.
- RAG fail-open is an explicit product setting. It does not weaken schema, novelty, compilation, test-case, authentication, or persistence checks.

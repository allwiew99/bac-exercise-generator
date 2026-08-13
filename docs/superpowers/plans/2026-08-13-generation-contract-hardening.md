# Generation Contract Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make eight representative RAG generations novel, bounded, fully executable through stdin/stdout, and validated in the real isolated Cloud Run sandbox without deploying the production service.

**Architecture:** Strengthen the prompt and deterministic validator at the generation boundary, return both rendered context and ordered chunks from the lazy RAG provider, and feed a centralized lexical novelty validator into the existing `ExerciseService` retry loop. Extend the E2E evaluator with exact-UID cleanup, and validate `SandboxCodeRunner` through a no-secret Cloud Run Job using `sandboxLauncher`.

**Tech Stack:** Python 3.12, Pydantic, Google Gen AI SDK, Vertex AI Gemini 2.5 Flash, Pinecone, SQLAlchemy/PostgreSQL, Cloud Build, Cloud Run Jobs sandbox launcher, pytest, mypy, Ruff.

## Global Constraints

- Do not change corpus contents or upsert/delete Pinecone vectors.
- Do not change metadata fallback, Pinecone ordering, reranker strategy, or Discovery Engine configuration.
- Keep `RERANKER_ENABLED=false` and require zero reranker construction attempts.
- Do not deploy a production Cloud Run service revision.
- Use `gemini_max_output_tokens=8192`.
- Production novelty policy is exact match OR token Jaccard `>=0.60` OR five-token shingle containment `>=0.60`.
- E2E database writes use a unique validation UID and are deleted by exact UID before completion.

---

### Task 1: Executable generation contracts

**Files:**
- Modify: `src/bac_generator/ai/prompt_builder.py`
- Modify: `src/bac_generator/services/exercise_validator.py`
- Modify: `tests/unit/test_prompt_builder.py`
- Modify: `tests/unit/test_exercise_validator.py`

**Interfaces:**
- Consumes: `ExerciseRequest`, `ExerciseResponse.solution`.
- Produces: deterministic `_validate_executable_contract(solution: str) -> None` behavior inside `ExerciseValidator.validate()`.

- [ ] **Step 1: Write failing prompt tests** asserting the initial and repair prompts require a complete C++17 program with `main()`, stdin/stdout-only I/O, file-topic stream wording, and a `main()` harness for subprogram topics.
- [ ] **Step 2: Verify RED** with `.venv/bin/pytest -q tests/unit/test_prompt_builder.py`; expect missing-contract assertion failures.
- [ ] **Step 3: Add the minimal prompt contract** once in the base prompt so repair prompts inherit it, including concise output-size expectations.
- [ ] **Step 4: Verify GREEN** with the same prompt tests.
- [ ] **Step 5: Write failing validator tests** for missing `main()`, `ifstream`, `ofstream`, `fstream`, `freopen`, `.open(...)`, and a hard-coded `bac.txt`, plus acceptance of stdin/stdout and a function with a `main()` harness.
- [ ] **Step 6: Verify RED** with `.venv/bin/pytest -q tests/unit/test_exercise_validator.py`; expect invalid solutions to reach the fake code validator instead of raising.
- [ ] **Step 7: Implement deterministic preflight checks** before compiler invocation with repair-oriented `ExerciseValidationError` messages.
- [ ] **Step 8: Verify GREEN** for prompt and validator tests.

### Task 2: Ordered RAG references and production novelty guard

**Files:**
- Create: `src/bac_generator/ai/retrieval/novelty.py`
- Create: `src/bac_generator/services/exercise_novelty_validator.py`
- Modify: `src/bac_generator/services/rag_context_provider.py`
- Modify: `src/bac_generator/services/exercise_service.py`
- Modify: `src/bac_generator/api/routes/exercises.py`
- Modify: `src/bac_generator/evaluation/rag/novelty.py`
- Modify: `tests/unit/test_rag_context_provider.py`
- Modify: `tests/unit/test_exercise_service.py`
- Create: `tests/unit/test_exercise_novelty_validator.py`
- Modify: `tests/integration/test_exercises.py`

**Interfaces:**
- Produces: `NoveltyPolicy`, `ReferenceSimilarity`, `evaluate_reference_similarity()`, `RagContext(text, chunks)`, and `ExerciseNoveltyValidator.validate(exercise, references)`.
- Consumes: ordered `RetrievedChunk` candidates and generated `ExerciseResponse`.

- [ ] **Step 1: Write failing novelty-policy tests** for the prior `0.7476` case, exact matches, Jaccard/shingle boundaries at exactly `0.60`, ordinary topic vocabulary, safe ID/score-only errors, and internal-evaluator fail-open logging.
- [ ] **Step 2: Verify RED** with the focused novelty-validator test; expect missing production module.
- [ ] **Step 3: Move shared lexical primitives** to `ai/retrieval/novelty.py`, keep evaluation diagnostics compatible, and implement the centralized production policy and validator.
- [ ] **Step 4: Verify GREEN** for evaluation and production novelty tests.
- [ ] **Step 5: Update provider tests first** to expect `RagContext`, ordered references, empty disabled/fail-open results, preserved Pinecone order, and zero reranker construction.
- [ ] **Step 6: Verify RED** because the provider still returns `str`.
- [ ] **Step 7: Implement `RagContext`** and return the exact context candidate list without mutable request-global state.
- [ ] **Step 8: Update service tests first** so suspicious output triggers the existing repair prompt and second attempt, accepted output validates normally, empty RAG works, and novelty internal errors do not block generation.
- [ ] **Step 9: Verify RED** because `ExerciseService` does not invoke the novelty validator.
- [ ] **Step 10: Integrate the validator** before compiler validation inside the existing `ExerciseValidationError` retry block, then wire it through FastAPI dependencies.
- [ ] **Step 11: Verify GREEN** across provider, service, novelty, and route tests.

### Task 3: Bounded Gemini output

**Files:**
- Modify: `src/bac_generator/core/config.py`
- Modify: `src/bac_generator/ai/gemini_client.py`
- Modify: `src/bac_generator/api/routes/exercises.py`
- Modify: `.env.example`
- Modify: `tests/unit/test_config.py`
- Create: `tests/unit/test_gemini_client.py`

**Interfaces:**
- `GeminiClient(..., max_output_tokens: int)` forwards the bound to `types.GenerateContentConfig`.

- [ ] **Step 1: Write failing config and client tests** asserting the default is `8192`, positive validation, and the SDK request receives exactly `8192`.
- [ ] **Step 2: Verify RED** because the setting and constructor argument are absent.
- [ ] **Step 3: Implement the setting and request bound**, wire the route factory, and document the environment variable.
- [ ] **Step 4: Verify GREEN** for config/Gemini tests and existing client consumers.

### Task 4: Isolated persistence and E2E report updates

**Files:**
- Modify: `src/bac_generator/evaluation/rag/generation_e2e.py`
- Modify: `scripts/validate_rag_e2e.py`
- Create: `tests/unit/evaluation/rag/test_generation_e2e.py`

**Interfaces:**
- Produces report fields `validation_user_id`, `inserted_ids`, `inserted_count`, `deleted_count`, `cleanup_completed`, `remaining_rows`, and `cleanup_sql`.

- [ ] **Step 1: Write failing cleanup tests** using a fake persistence boundary: exact UID only, every inserted ID reported, cleanup in a `finally` path, and zero remaining rows required.
- [ ] **Step 2: Verify RED** because current E2E records are retained.
- [ ] **Step 3: Add a focused cleanup function** using SQLAlchemy `delete(Exercise).where(Exercise.user_id == validation_uid)`, commit it, and count remaining exact-UID rows.
- [ ] **Step 4: Update the E2E composition** for `RagContext`, novelty validation, bounded Gemini construction, failure-safe cleanup, and acceptance criteria.
- [ ] **Step 5: Verify GREEN** for E2E unit tests without external API calls.

### Task 5: Real Cloud Run sandbox validation job

**Files:**
- Create: `src/bac_generator/evaluation/sandbox_validation.py`
- Create: `tests/unit/evaluation/test_sandbox_validation.py`
- Generate cloud artifact: uniquely tagged validation image and `bac-rag-sandbox-validation` Cloud Run Job.

**Interfaces:**
- `run_sandbox_validation() -> SandboxValidationReport` checks binary presence, successful stdin/stdout execution, mounted-workspace path through the runner, nonzero rejection, and timeout rejection.

- [ ] **Step 1: Write failing unit tests** for all five report outcomes with a controlled runner boundary.
- [ ] **Step 2: Verify RED** because the module is absent.
- [ ] **Step 3: Implement the validation module** using real `SandboxCodeRunner` operations and a JSON/console report.
- [ ] **Step 4: Verify GREEN** locally with the sandbox subprocess boundary mocked.
- [ ] **Step 5: Run Cloud Build** with a unique non-production image tag.
- [ ] **Step 6: Deploy/update only the isolated job** with `--sandbox-launcher`, no secrets, no retries, and a bounded timeout.
- [ ] **Step 7: Execute the job and collect logs** proving all five checks pass; do not update the production service.

### Task 6: Live eight-case rerun and verification

**Files:**
- Regenerate: `data/rag/evaluation/generation_e2e_report.json`

- [ ] **Step 1: Run the eight-case E2E CLI** with the production database exact-UID cleanup enabled.
- [ ] **Step 2: Validate acceptance criteria**: 8/8 success, context present, five chunks, Pinecone order, zero novelty flags, zero reranker calls, fail-open/closed pass, and zero retained validation rows.
- [ ] **Step 3: Verify Pinecone post-run** remains one namespace and exactly 317 vectors.
- [ ] **Step 4: Run `py_compile`** over all Python files under `src`, `scripts`, and `tests`.
- [ ] **Step 5: Run strict mypy** with `.venv/bin/mypy src scripts tests`.
- [ ] **Step 6: Run Ruff** with `.venv/bin/ruff check .`.
- [ ] **Step 7: Run focused tests** for prompts, validators, novelty, RAG, Gemini, E2E, and sandbox.
- [ ] **Step 8: Run the full suite** with `.venv/bin/pytest -q` and report exact results.
- [ ] **Step 9: Stop before production deployment** and recommend readiness only from the collected evidence.

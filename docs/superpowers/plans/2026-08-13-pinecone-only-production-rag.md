# Pinecone-Only Production RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Pinecone ordering the default generation-time RAG behavior while retaining lazy, opt-in Discovery Engine reranking and complete RAG fail-open coverage.

**Architecture:** A new `RagContextProvider` owns lazy construction, retrieval, optional reranking, context selection, and fail-open behavior. `ExerciseService` depends on its protocol, and FastAPI injects only a lightweight provider whose external factories execute during generation, never during unrelated GET requests.

**Tech Stack:** Python 3.12, FastAPI dependencies, Pydantic settings, pytest/pytest-asyncio, strict mypy, ruff.

## Global Constraints

- Default `reranker_enabled` to `False` and retain an explicit opt-in experiment path.
- Do not delete the reranker, Discovery Engine dependency, evaluation framework, dataset, or report.
- Do not modify the corpus, Pinecone contents, deployment configuration, or production deployment state.
- Preserve Pinecone order when reranking is disabled.
- Ensure initialization, retrieval, reranking, and context failures honor `rag_fail_open`.
- Avoid broad route/application exception swallowing.

---

### Task 1: Lazy RAG context provider

**Files:**
- Create: `src/bac_generator/services/rag_context_provider.py`
- Create: `tests/unit/test_rag_context_provider.py`

**Interfaces:**
- Produces: `RagContextProviderProtocol.get_context(query, topic, difficulty) -> str` and `RagContextProvider` accepting retrieval/reranker factories plus explicit feature flags.

- [ ] Write failing tests proving that disabled RAG invokes no factories; disabled reranking invokes retrieval only and passes original-order candidates to `ContextBuilder`; enabled reranking passes reranked results; initialization/retrieval failures follow fail-open/fail-closed.
- [ ] Run `pytest -q tests/unit/test_rag_context_provider.py` and verify failure because the provider does not exist.
- [ ] Implement the provider with a narrow exception boundary around only the optional RAG subsystem.
- [ ] Re-run the focused tests and verify they pass.

### Task 2: ExerciseService integration

**Files:**
- Modify: `src/bac_generator/services/exercise_service.py`
- Modify: `tests/unit/test_exercise_service.py`

**Interfaces:**
- Consumes: `RagContextProviderProtocol`.
- Produces: generation that requests context once while preserving retry/persistence behavior.

- [ ] Replace the existing success/fail-open unit expectations with failing tests asserting provider context reaches the prompt and provider failures propagate only when the provider is configured fail-closed.
- [ ] Run the affected `ExerciseService` tests and verify the expected constructor/behavior failures.
- [ ] Replace concrete retrieval/reranker/context dependencies with the provider protocol and remove the now-duplicated inner RAG exception block.
- [ ] Re-run all `ExerciseService` tests and verify they pass.

### Task 3: Lazy FastAPI dependency wiring

**Files:**
- Modify: `src/bac_generator/api/routes/exercises.py`
- Modify: `tests/integration/test_exercises.py`

**Interfaces:**
- Produces: `get_rag_context_provider()` storing `get_retrieval_service` and `get_reranker` as factories without invoking them during dependency resolution.

- [ ] Write failing integration tests proving list/get endpoints do not construct cloud RAG clients and generation fails open when the lazy retrieval factory raises during initialization.
- [ ] Run those integration tests and verify failure under the eager dependency graph.
- [ ] Simplify concrete retrieval construction to a plain factory, add the provider dependency, and inject it into `ExerciseService`.
- [ ] Re-run focused route tests and verify GET and fail-open generation behavior.

### Task 4: Default configuration

**Files:**
- Modify: `src/bac_generator/core/config.py`
- Modify: `.env.example`
- Modify: `tests/unit/test_config.py`

**Interfaces:**
- Produces: default `reranker_enabled=False`, with `RERANKER_ENABLED=false` documented for deployment environments.

- [ ] Add a failing default-settings assertion for disabled reranking.
- [ ] Run the config test and verify it fails against the current `True` default.
- [ ] Change the Pydantic default and example environment value without touching deployment configuration.
- [ ] Re-run the config test and verify it passes.

### Task 5: Quality and scope gate

**Files:**
- Verify: all modified/new Python files and focused tests.

- [ ] Run `py_compile` on modified/new Python files.
- [ ] Run strict `mypy` on modified/new Python files.
- [ ] Run `ruff check` on modified/new Python files.
- [ ] Run focused RAG/provider/service/route/config tests.
- [ ] Run the complete repository pytest suite.
- [ ] Verify the corpus SHA is unchanged and no ingestion/deployment command was executed.
- [ ] Inspect the final diff to confirm the reranker implementation, dependency, and evaluation artifacts remain present.

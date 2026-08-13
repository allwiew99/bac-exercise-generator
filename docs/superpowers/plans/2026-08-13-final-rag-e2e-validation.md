# Final RAG E2E Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate eight real Gemini generations against the live 317-document Pinecone namespace while proving Pinecone-only ordering, context injection, validation, compilation/runtime, persistence, novelty, and fail-open behavior.

**Architecture:** Keep production behavior unchanged. Add a deterministic lexical novelty evaluator under the existing RAG evaluation package and a thin E2E validation runner that composes real production services with tracing wrappers at their public boundaries. Store only metadata, scores, generated statements, and similarity summaries in the report; never log full reference contents.

**Tech Stack:** Python 3.12, Pydantic, Vertex AI Gemini, Pinecone, SQLAlchemy/PostgreSQL, Clang or Cloud Run sandbox through the configured `CodeRunnerProtocol`, pytest, mypy, Ruff.

## Global Constraints

- Use the live `bac-exercises-rag` index and configured namespace read-only; do not upsert or delete vectors.
- Require exactly 317 vectors before generation.
- Keep `RERANKER_ENABLED=false`; a forbidden factory must prove Discovery Engine construction never occurs.
- Do not deploy or modify parser rules, corpus files, production RAG ranking, or reranker implementation.
- Persist only successfully validated E2E exercises through `ExerciseRepository` and report their IDs.
- Report the configured code runner accurately; never label local Clang execution as Cloud Run sandbox execution.

---

### Task 1: Deterministic novelty evaluation

**Files:**
- Create: `src/bac_generator/evaluation/rag/novelty.py`
- Create: `tests/unit/evaluation/rag/test_novelty.py`

**Interfaces:**
- Consumes: `ExerciseResponse`, `RetrievedChunk`.
- Produces: `normalize_for_similarity(text)`, `evaluate_reference_similarity(exercise, reference)`, and `find_highest_reference_similarity(exercise, references)`.

- [ ] **Step 1: Write failing tests** for Unicode normalization, exact copying, near-copy shingle containment, copied test cases, deterministic highest-match selection, and empty references.
- [ ] **Step 2: Verify RED** with `.venv/bin/pytest -q tests/unit/evaluation/rag/test_novelty.py`; expect import failure because the module does not exist.
- [ ] **Step 3: Implement the evaluator** with NFKC/case-folded word normalization, token Jaccard, five-token shingle containment, numeric constant intersection, and test-case occurrence checks.
- [ ] **Step 4: Verify GREEN** with the same pytest command; expect six passing tests.

### Task 2: Auditable live E2E runner

**Files:**
- Create: `src/bac_generator/evaluation/rag/generation_e2e.py`
- Create: `scripts/validate_rag_e2e.py`
- Create at runtime: `data/rag/evaluation/generation_e2e_report.json`

**Interfaces:**
- Consumes: production `RetrievalService`, `RagContextProvider`, `ContextBuilder`, `PromptBuilder`, `GeminiClient`, `ExerciseValidator`, `CodeValidator`, `ExerciseRepository`, and configured database session.
- Produces: `run_e2e_validation()` returning a typed report and a CLI that writes stable JSON.

- [ ] **Step 1: Add tracing wrappers** around vector queries, retrieval output, context construction, prompt construction, LLM calls, code-runner calls, and persistence. Wrappers delegate to real implementations and record only identifiers, scores, counts, flags, and errors.
- [ ] **Step 2: Define eight cases** for pseudocode, arrays, matrices, files, graphs, number processing, subprograms, and binary search using easy/medium/hard difficulty values.
- [ ] **Step 3: Run each case sequentially** through `ExerciseService`; reconstruct the validated response from the persisted ORM entity, calculate highest novelty similarity against all eight retrieved candidates, and retain failures without aborting the report.
- [ ] **Step 4: Add controlled fail-open validation** using a retrieval factory that raises before embedding/Pinecone. With fail-open enabled, require empty context followed by real Gemini generation, validation, code execution, and persistence. With fail-open disabled, require the same error to propagate before any Gemini call.
- [ ] **Step 5: Assert preflight invariants**: 317 vectors, sole configured namespace, 768 dimensions, cosine metric, and reranker disabled. Exit nonzero after writing the report if any invariant or behavioral validation fails.
- [ ] **Step 6: Run live validation** with `.venv/bin/python scripts/validate_rag_e2e.py`; record elapsed time and the report path.

### Task 3: Complete verification

**Files:**
- Verify all new/modified Python files and the generated report.

- [ ] **Step 1: Run compilation** with `.venv/bin/python -m py_compile` over the novelty module, E2E module, CLI, and their tests.
- [ ] **Step 2: Run strict typing** with `.venv/bin/mypy src scripts tests`; expect no issues.
- [ ] **Step 3: Run lint** with `.venv/bin/ruff check .`; expect no errors.
- [ ] **Step 4: Run focused tests** for novelty, provider, retrieval, service, sandbox, and E2E boundaries.
- [ ] **Step 5: Run the full suite** with `.venv/bin/pytest -q`; expect zero failures.
- [ ] **Step 6: Review the report** against all twelve requested reporting items and make no deployment changes.

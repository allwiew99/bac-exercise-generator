# RAG Retrieval Correctness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the full test suite and make filtered RAG retrieval fail open to semantic retrieval when sparse metadata yields too few candidates.

**Architecture:** Keep production generation behavior unchanged and update `ExerciseService` tests with reusable, observable RAG fakes. Implement fallback orchestration inside `RetrievalService`, reusing one embedding and the existing vector-repository interface, then review a stratified corpus sample without modifying it.

**Tech Stack:** Python 3.12, asyncio, Pydantic, pytest, mypy strict, Ruff.

## Global Constraints

- Do not ingest or upsert anything into Pinecone.
- Do not modify `data/rag/bac_corpus.preview.json`.
- Do not bypass the `ExerciseService` RAG constructor dependencies.
- Do not weaken existing assertions or production fail-open behavior.
- Use the same query embedding for filtered and fallback vector queries.
- Only fall back when metadata filters exist and the filtered result count is below `top_k`.

---

### Task 1: ExerciseService RAG test collaborators and paths

**Files:**
- Modify: `tests/unit/test_exercise_service.py`

**Interfaces:**
- Test-only `FakeRetrievalService`, `FakeReranker`, and `FakeContextBuilder` subclass their production collaborators without constructing external clients.
- A reusable service factory supplies all required dependencies to every generation test.

- [ ] Add reusable successful RAG fakes and update all four existing service constructions.
- [ ] Run the four existing tests and verify the constructor failures are gone without production changes.
- [ ] Add a successful-context test that asserts retrieval arguments, reranking, context construction, and reference content in the LLM prompt.
- [ ] Add a failing-retrieval test that asserts generation succeeds without reference context when fail-open is enabled.
- [ ] Run the focused ExerciseService tests until green.

### Task 2: Sparse-metadata retrieval fallback

**Files:**
- Modify: `src/bac_generator/services/retrieval_service.py`
- Create: `tests/unit/test_retrieval_service.py`

**Interfaces:**
- `RetrievalService.retrieve(...)` retains its public signature.
- Filtered retrieval is sufficient at `len(chunks) >= effective_top_k`.
- `_merge_chunks(...)` keeps the highest-scoring chunk for each ID and returns no more than `top_k` chunks in descending score order.

- [ ] Add failing tests for sufficient filtered results, insufficient filtered results, no-filter behavior, duplicate merging, best-score retention, result cap, one embedding, empty query, and zero/negative `top_k`.
- [ ] Run the new tests and confirm failures identify missing fallback and zero validation.
- [ ] Fix explicit `top_k` selection so zero remains invalid.
- [ ] Add filtered-result threshold, warning log, same-vector fallback query, and deterministic merging.
- [ ] Run retrieval and ExerciseService focused tests until green.

### Task 3: Stratified preview review and quality gates

**Files:**
- Read only: `data/rag/bac_corpus.preview.json`

**Interfaces:**
- Select at least 20 documents across years, MI/SN IDs, all three sections, classified/unclassified topics, pseudocode, and mathematical notation.
- Produce review evidence without rewriting the JSON.

- [ ] Select and inspect the stratified sample, recording IDs and any boundary, notation, boilerplate, or barem issues.
- [ ] Run `py_compile` for modified Python files.
- [ ] Run strict `mypy` for modified Python files.
- [ ] Run Ruff for modified Python files.
- [ ] Run focused tests and the full repository test suite.
- [ ] Confirm preview checksum is unchanged and no Pinecone ingestion command was run.

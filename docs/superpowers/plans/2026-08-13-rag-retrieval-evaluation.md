# RAG Retrieval Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and run a group-aware, auditable comparison of Pinecone top-8 retrieval against Discovery Engine reranking of the identical candidates.

**Architecture:** Pure typed metric and aggregation modules consume a corpus-validated golden JSON dataset. An injected asynchronous evaluator measures the existing `RetrievalService` and `Reranker`; a thin CLI supplies live clients and writes deterministic JSON output.

**Tech Stack:** Python 3.12, Pydantic, asyncio, pytest/pytest-asyncio, Pinecone, Vertex embeddings, Google Discovery Engine.

## Global Constraints

- Do not modify the corpus, re-ingest Pinecone, deploy, or change production RAG behavior/configuration.
- Recall, MRR, and nDCG operate on relevance groups; duplicate equivalent documents never receive extra credit.
- Baseline uses top five of one Pinecone top-8 result; reranking receives that exact top-8 list.
- Console and JSON reports expose `successful_queries / total_queries` and `failed_queries / total_queries`.
- External services are mocked in unit tests.

---

### Task 1: Group-aware metrics and typed models

**Files:**
- Create: `src/bac_generator/evaluation/rag/models.py`
- Create: `src/bac_generator/evaluation/rag/metrics.py`
- Create: `tests/unit/evaluation/rag/test_metrics.py`

**Interfaces:**
- Produces: `RelevanceGroup`, `GoldenQuery`, `GoldenDataset`, `RankingMetrics`, and `evaluate_ranking(ids, groups, cutoff)`.

- [ ] Write literal tests proving group-level Recall, first-hit MRR, graded nDCG, cutoff behavior, and duplicate-group suppression.
- [ ] Run the focused test and verify failure because the modules do not exist.
- [ ] Implement Pydantic models and pure metric calculation with gain `2**grade - 1`.
- [ ] Run the focused test and verify it passes.

### Task 2: Corpus-aware dataset validation

**Files:**
- Create: `src/bac_generator/evaluation/rag/dataset.py`
- Create: `tests/unit/evaluation/rag/test_dataset.py`

**Interfaces:**
- Consumes: `GoldenDataset`, `RetrievalDocument`.
- Produces: `load_golden_dataset(path, corpus_documents)`.

- [ ] Write tests for a valid dataset, unknown relevant IDs, duplicate query IDs, duplicate group IDs, duplicate document membership, and empty labels.
- [ ] Run tests and verify the expected import/behavior failures.
- [ ] Implement JSON/Pydantic loading and explicit corpus-ID integrity checks with actionable errors.
- [ ] Run focused tests and verify they pass.

### Task 3: Deterministic aggregation and reporting

**Files:**
- Create: `src/bac_generator/evaluation/rag/aggregator.py`
- Create: `src/bac_generator/evaluation/rag/reporting.py`
- Create: `tests/unit/evaluation/rag/test_aggregator.py`
- Create: `tests/unit/evaluation/rag/test_reporting.py`

**Interfaces:**
- Produces: per-query comparison classification, macro aggregate/per-topic summaries, latency summaries, stable report JSON, and console summary.

- [ ] Write hand-derived tests for improved/unchanged/degraded counts, macro topic metrics, percentile latency, stable ordering, and visible success/failure ratios.
- [ ] Run tests and verify failure because aggregation/reporting are absent.
- [ ] Implement deterministic aggregation and serialization.
- [ ] Run focused tests and verify they pass.

### Task 4: Injected evaluator orchestration

**Files:**
- Create: `src/bac_generator/evaluation/rag/evaluator.py`
- Create: `tests/unit/evaluation/rag/test_evaluator.py`
- Modify: `src/bac_generator/evaluation/rag/__init__.py`

**Interfaces:**
- Consumes: retrieval/reranker protocols, golden queries, and injected monotonic clock.
- Produces: `RagRetrievalEvaluator.evaluate(dataset)` with per-query results and explicit stage failures.

- [ ] Write asynchronous tests proving one top-8 retrieval, identity-preserved reranker candidates, top-5/top-8 metrics, deterministic timing, and continued execution after stage failures.
- [ ] Run tests and verify failure because evaluator behavior is absent.
- [ ] Implement the minimal orchestration and protocols required by the tests.
- [ ] Run focused tests and verify they pass.

### Task 5: Auditable 30-query golden set

**Files:**
- Create: `data/rag/evaluation/retrieval_golden.json`

**Interfaces:**
- Consumes: the 317-document `data/rag/bac_corpus.json`.
- Produces: approximately 30 labeled queries spanning required Bac topics with explicit document IDs and rationales.

- [ ] Inspect corpus documents by topic and intent, including near-duplicate MI/SN/language variants.
- [ ] Author queries and distinct relevance groups only from inspected content.
- [ ] Load the complete dataset through `load_golden_dataset` to verify every ID and grouping invariant.
- [ ] Print and inspect coverage counts; include recursion only if corpus support is defensible.

### Task 6: Live CLI and report artifact

**Files:**
- Create: `scripts/evaluate_rag_retrieval.py`
- Create at runtime: `data/rag/evaluation/retrieval_evaluation_report.json`
- Create: `tests/unit/evaluation/rag/test_cli.py`

**Interfaces:**
- Wires `VertexEmbeddingClient`, `PineconeRepository`, `RetrievalService`, and `Reranker` into the evaluator.

- [ ] Write a CLI-boundary test using injected/fake evaluation dependencies and assert nonzero exit on partial failure plus visible query ratios.
- [ ] Run the test and verify the expected failure.
- [ ] Implement argument parsing, validated loading, live wiring, report writing, console output, and failure exit status.
- [ ] Run focused tests and verify they pass.
- [ ] Run the live evaluation sequentially and preserve its report artifact.

### Task 7: Quality gate and analysis

**Files:**
- Inspect: all files created above and the live JSON report.

- [ ] Run `py_compile` on all new Python files.
- [ ] Run strict `mypy` on all new Python files.
- [ ] Run `ruff check` on all modified/new Python files.
- [ ] Run focused evaluation tests.
- [ ] Run the full repository pytest suite.
- [ ] Verify no corpus file, production RAG behavior, Pinecone data, or deployment configuration changed.
- [ ] Analyze aggregate/per-topic metrics, query outcomes, latency, candidate failures, and concrete reranker failure cases.
- [ ] Recommend global reranking, conditional reranking, Pinecone-only ranking, or another tuning pass based on measured evidence.

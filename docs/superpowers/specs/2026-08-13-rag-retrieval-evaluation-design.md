# RAG Retrieval Evaluation Design

## Purpose

Build a repeatable, manually auditable offline evaluation that compares the
existing Pinecone retrieval ordering with Discovery Engine reranking over the
same candidate set. The evaluation measures quality and latency without
changing corpus contents, Pinecone vectors, production retrieval behavior,
reranker configuration, or deployment configuration.

## Scope and constraints

- Evaluate approximately 30 realistic Romanian Bac Informatics queries.
- Cover pseudocode, arrays, matrices, strings, files, graphs, trees,
  subprograms, number processing, divisibility, combinatorics/backtracking,
  binary search, unclassified retrieval, and recursion only where the corpus
  contains defensible support.
- Retrieve exactly one top-8 candidate set per query through the existing
  `RetrievalService`.
- Evaluate the first five Pinecone candidates as the baseline.
- Pass that unchanged top-8 list to the existing `Reranker` and evaluate its
  returned top five.
- Use relevance groups so equivalent MI/SN or programming-language variants
  can satisfy one judgment without receiving duplicate metric credit.
- Use real external services only in the live evaluation command; unit tests
  inject fakes.
- Do not modify the corpus, ingest vectors, deploy, or change production RAG
  configuration.

## Golden dataset

The version-controlled dataset lives at
`data/rag/evaluation/retrieval_golden.json`. Each query contains:

- a stable query ID;
- realistic Romanian query text;
- an evaluation topic used for coverage and per-topic aggregation;
- an optional production topic filter;
- one or more relevance groups.

Each relevance group contains:

- a stable group ID local to the query;
- an integer relevance grade from 1 to 3;
- every equivalent underlying corpus document ID;
- a concise manual-judgment rationale.

Grade 3 means a direct match for the complete retrieval intent, grade 2 means
a strong but incomplete match, and grade 1 means a useful supporting match.
Only inspected corpus documents receive labels. Merely similar exercises stay
in distinct groups. A document ID may occur in only one group for a query.

Dataset loading validates query and group uniqueness, positive grades, nonempty
texts and groups, and every labeled document ID against the current
`RetrievalDocument` corpus. Unknown IDs are a hard error.

## Group-aware metrics

Metrics operate on relevance groups, not literal document IDs. While walking a
ranking, the first retrieved document belonging to a relevant group claims that
group; later documents from the same group contribute no additional gain.

- `Recall@k`: claimed relevant groups divided by all relevant groups.
- `MRR@k`: reciprocal rank of the first document that claims any relevant
  group, or zero when no group is matched.
- `nDCG@k`: DCG from the first claim of each group using gain
  `2**grade - 1`, divided by the ideal ordering of group grades.
- `Recall@8`: baseline candidate coverage, used to separate candidate-generation
  failures from top-five ordering failures.

Raw retrieved-document counts and duplicate-group hits may be included for
debugging but are not primary quality metrics.

## Runtime architecture

The package `src/bac_generator/evaluation/rag/` contains focused modules:

- `models.py`: Pydantic dataset, metric, latency, query-result, and report
  models.
- `dataset.py`: JSON loading and corpus-aware validation.
- `metrics.py`: pure group-aware metric functions.
- `aggregator.py`: deterministic aggregate and per-topic summaries plus query
  outcome classification.
- `evaluator.py`: orchestration over injected `RetrievalService`, `Reranker`,
  and monotonic clock.
- `reporting.py`: stable JSON serialization and concise console summary.

The script `scripts/evaluate_rag_retrieval.py` wires real Vertex embeddings,
Pinecone, and Discovery Engine into the evaluator. It loads the production
corpus only for ID validation, runs queries sequentially to keep service load
controlled, and writes an evaluation report under `data/rag/evaluation/`.

For each query the evaluator records retrieval latency around the single
`RetrievalService.retrieve(..., top_k=8)` call and reranker latency around the
single `Reranker.rerank(query, candidates)` call. Combined latency is their
sum. Reports include mean, median, p95, minimum, and maximum milliseconds for
retrieval, reranking, and combined execution.

## Comparison rule

The primary per-query comparison is the delta in `nDCG@5`:

- improved when reranked nDCG exceeds baseline by more than `1e-9`;
- degraded when it is lower by more than `1e-9`;
- unchanged otherwise.

Recall and MRR remain visible for diagnosing why ordering changed. Aggregate
metrics are macro averages over queries, and per-topic metrics are macro
averages over queries assigned to that evaluation topic. Output order is stable
by query ID and topic so aggregation is deterministic for identical inputs.

## Failure handling

Dataset or corpus-integrity errors fail before external calls. A live query
failure is recorded with its query ID and stage (`retrieval` or `reranking`),
then the run continues so one API failure does not erase other measurements.
Failed queries are excluded from quality and latency aggregates and are counted
explicitly. The script exits nonzero when any query fails, preventing an
apparently complete report from hiding partial execution.

## Tests

Unit tests use literal, hand-checked rankings and mocked external boundaries.
They cover:

- Recall, MRR, and nDCG for hits, misses, grades, cutoffs, and duplicate IDs
  within one relevance group;
- dataset acceptance plus duplicate query/group IDs and unknown corpus IDs;
- proof that reranking receives the exact top-8 objects returned by retrieval;
- top-five versus top-eight evaluation behavior and injected latency timing;
- deterministic aggregate/per-topic results and improved/unchanged/degraded
  classification;
- report serialization stability.

The final quality gate runs `py_compile`, strict `mypy`, `ruff`, focused
evaluation tests, and the complete pytest suite before results are reported.

## Production recommendation

The evaluation does not alter runtime behavior. The final report recommends
one of: global reranking, conditional reranking, Pinecone-only ranking, or
another tuning pass. The recommendation is based on aggregate and per-topic
quality, the improved/unchanged/degraded distribution, candidate Recall@8,
observed latency, and inspected failure cases rather than a single aggregate
number.

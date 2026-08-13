# Production RAG Architecture

## Runtime flow

```text
Authenticated generation request
        |
        v
Lazy RAG context provider
        |
        v
Vertex AI / gemini-embedding-001 (768 dimensions)
        |
        v
Pinecone / bac-exercises-rag / bac-exercises
        |
        +-- filtered metadata query
        |       |
        |       +-- fewer than top_k -> unfiltered semantic fallback
        |
        v
Pinecone score ordering (top candidates)
        |
        v
ContextBuilder
        |
        v
PromptBuilder + deterministic novelty guard
        |
        v
Gemini 2.5 Flash (structured JSON, max 8,192 output tokens)
        |
        v
ExerciseValidator + CodeValidator
        |
        v
Cloud Run sandboxLauncher / clang++ / lld / C++17 tests
        |
        v
PostgreSQL persistence
```

Discovery Engine reranking is retained for experiments but is disabled in the
production hot path (`RERANKER_ENABLED=false`). Pinecone ordering is passed
unchanged to `ContextBuilder`.

## Corpus and ingestion

The production namespace contains 317 exercise-level retrieval documents built
from real Romanian Bacalaureate Informatics PDFs. The deterministic ingestion
pipeline extracts PDF text with layout information, classifies subjects and
grading guides, normalizes known extraction artifacts, and preserves semantic
exercise boundaries. Subject and grading-guide content are never merged.

Unsafe chunks are excluded rather than guessed. This includes exercises that
require a missing diagram and notation or multi-column pseudocode that cannot be
reconstructed confidently. Stable IDs encode the detected exam metadata and
exercise position. Ambiguous topic classification uses `topic="unclassified"`;
difficulty is not invented.

The approved production corpus is `data/rag/bac_corpus.json`, containing 317
schema-valid documents and 317 unique IDs. Its SHA-256 is
`e47ba07115179f6086b88937554f845abe80291546edab71b3dfa5a5d79692b0`.

## Retrieval behavior and failure policy

Generation embeds each retrieval query exactly once. When topic or difficulty
metadata is available, Pinecone is queried with those filters first. If fewer
than `top_k` candidates are returned, the service reuses the same embedding for
an unfiltered semantic query, merges candidates by document ID, preserves the
best duplicate score, and returns at most `top_k` results.

RAG is fail-open in production. Initialization, embedding, or retrieval failure
is logged without reference text and generation continues with an empty RAG
context. The fail-closed mode remains covered for controlled validation.
Dependencies are lazy: unrelated list/get endpoints do not initialize Vertex,
Pinecone, or Discovery Engine clients.

## Retrieval evaluation

The auditable golden set contains 30 realistic queries with explicit relevance
groups for equivalent MI/SN or programming-language variants. Metrics operate
on groups so equivalent duplicate documents do not inflate quality.

| Ranking | Recall@5 | MRR@5 | nDCG@5 | Recall@8 |
|---|---:|---:|---:|---:|
| Pinecone | 1.0000 | 1.0000 | 0.9946 | 1.0000 |
| Pinecone + Discovery Engine | 1.0000 | 0.9500 | 0.9508 | n/a |

All 30 queries completed. Reranking improved 1 query, left 24 unchanged, and
degraded 5. Mean measured latency was approximately 758 ms for Pinecone
retrieval, 221 ms for reranking, and 979 ms combined. The lower MRR/nDCG and
additional latency led to the production decision to keep Pinecone ranking
only. The reranker implementation, dependency, golden set, and report remain
available for future tuning.

## Novelty and generation contracts

Generated statements are compared with every retrieved reference using
normalized exact match, token Jaccard similarity, and five-token shingle
containment. A candidate enters the existing repair/retry flow when it is an
exact match, token Jaccard is at least 0.60, or shingle containment is at least
0.60. Internal novelty-evaluator failures are fail-open and log only reference
IDs and scores, never corpus contents.

Reference solutions are complete C++17 programs with `main()`. File-topic
exercises preserve Bac file-processing semantics while using stdin/stdout; file
streams, `freopen`, and named-file access are rejected. Subprogram tasks remain
student-facing Bac-style exercises, while their reference solutions include a
small executable `main()` harness.

## Sandbox validation and operations

Production uses `CODE_RUNNER_PROVIDER=sandbox` and Cloud Run
`sandboxLauncher`. The isolated validation path verifies compilation, stdin and
stdout, the mounted workspace, nonzero exits, and timeouts using clang++ and
lld. Only exercises whose reference solution passes all generated tests are
persisted.

Required production configuration:

- `RAG_ENABLED=true`
- `RAG_FAIL_OPEN=true`
- `RERANKER_ENABLED=false`
- `EMBEDDING_MODEL=gemini-embedding-001`
- `EMBEDDING_DIMENSIONS=768`
- `PINECONE_INDEX_NAME=bac-exercises-rag`
- `PINECONE_NAMESPACE=bac-exercises`
- `GEMINI_MAX_OUTPUT_TOKENS=8192`
- `CODE_RUNNER_PROVIDER=sandbox`

`PINECONE_API_KEY` and `DATABASE_URL` are injected from Google Secret Manager.
The corpus is not packaged into the runtime image; production retrieval reads
the already-ingested Pinecone namespace.

# Bac Exercise Generator

A production-oriented application that retrieves real Romanian Bacalaureate
Informatics exercises, generates a new exercise with Gemini, validates its C++17
reference solution in an isolated Cloud Run sandbox, and persists the result for
an authenticated user.

## Production capabilities

- Firebase authentication and per-user exercise ownership
- 317-document real Bac Informatics corpus in Pinecone
- Vertex AI `gemini-embedding-001` embeddings with 768 dimensions
- metadata-filtered retrieval with an unfiltered semantic fallback
- Pinecone score ordering (Discovery Engine reranking is disabled by default)
- deterministic statement novelty checks with repair/retry
- structured Gemini 2.5 Flash generation capped at 8,192 output tokens
- complete C++17 stdin/stdout reference programs, including file and subprogram topics
- Cloud Run `sandboxLauncher` execution with clang++ and lld
- PostgreSQL/Supabase persistence and automated Alembic migrations
- Redis-backed distributed rate limiting
- Next.js frontend on Cloud Run with production CORS restrictions
- GitHub Actions CI/CD and Google Secret Manager

## Production generation flow

```text
User request
    -> lazy RAG initialization
    -> Vertex embedding
    -> Pinecone metadata-filtered retrieval
    -> semantic fallback when the filtered result is sparse
    -> Pinecone-ranked candidates
    -> ContextBuilder
    -> PromptBuilder
    -> novelty guard
    -> Gemini
    -> ExerciseValidator / CodeValidator
    -> Cloud Run sandbox
    -> PostgreSQL
```

Reranking is intentionally absent from the production hot path. An auditable
30-query evaluation measured lower MRR@5 and nDCG@5 after Discovery Engine
reranking, plus additional latency. The implementation and evaluation artifacts
remain in the repository for future experiments.

See [Production RAG Architecture](docs/architecture/production-rag.md) for the
corpus, retrieval, novelty, evaluation, failure, and sandbox details.

## Corpus and deterministic ingestion

The source PDFs are parsed into semantic exercise-level chunks. The parser uses
layout-aware deterministic rules to preserve exercise boundaries, Romanian
diacritics, mathematical notation, and reconstructable pseudocode. It keeps
subjects and grading guides separate and excludes unsafe chunks that require a
missing visual or cannot be reconstructed confidently.

The production corpus is `data/rag/bac_corpus.json`:

- documents: 317
- unique deterministic IDs: 317
- SHA-256: `e47ba07115179f6086b88937554f845abe80291546edab71b3dfa5a5d79692b0`
- Pinecone index: `bac-exercises-rag`
- namespace: `bac-exercises`
- metric: cosine

Build a review-only preview (this does not ingest Pinecone):

```bash
python scripts/build_rag_corpus.py
```

The ingestion command is intentionally separate:

```bash
python scripts/ingest_rag_corpus.py
```

## Retrieval evaluation

The golden dataset at `data/rag/evaluation/retrieval_golden.json` contains 30
manually auditable queries. Equivalent MI/SN or language variants are grouped,
so duplicates cannot inflate relevance metrics.

| Ranking | Recall@5 | MRR@5 | nDCG@5 | Recall@8 |
|---|---:|---:|---:|---:|
| Pinecone | 1.0000 | 1.0000 | 0.9946 | 1.0000 |
| Pinecone + reranker | 1.0000 | 0.9500 | 0.9508 | n/a |

Reranking improved 1 query, left 24 unchanged, and degraded 5. Mean latency was
approximately 758 ms for retrieval and another 221 ms for reranking. Production
therefore uses Pinecone ranking only (`RERANKER_ENABLED=false`).

Run the evaluation without changing runtime behavior:

```bash
python scripts/evaluate_rag_retrieval.py
```

## Generation and execution contracts

The generated `solution` is always a complete C++17 program with `main()`.
File-topic exercises use stdin/stdout even when the student-facing wording
models file processing; file streams, `freopen`, and named files are rejected.
Subprogram exercises retain Bac-style wording while the reference solution uses
a small `main()` harness to exercise the requested subprogram.

Every candidate must pass structured validation, business rules, compilation,
and all generated test cases before persistence. Statement novelty is rejected
and repaired when there is an exact match, token Jaccard similarity of at least
0.60, or five-token shingle containment of at least 0.60 against any retrieved
reference.

## API

```text
GET  /health
POST /exercises/generate
GET  /exercises/
GET  /exercises/{exercise_id}
POST /exercises/{exercise_id}/submissions
GET  /exercises/{exercise_id}/solution
```

All exercise and submission endpoints require a Firebase bearer token. Safe
exercise responses do not expose hidden tests, the reference solution, or its
explanation before the dedicated solution request.

Production rate limits are:

- generation: 10 requests per 60 seconds per user
- submissions: 30 requests per 60 seconds per user

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
docker compose up -d
alembic upgrade head
uvicorn bac_generator.main:app --reload
```

The default local providers are Ollama, the local C++ runner, an in-memory rate
limiter, and a local PostgreSQL URL. Supply Vertex/Pinecone credentials only for
explicit live RAG validation.

Frontend development:

```bash
cd frontend
npm install
npm run dev
```

## Configuration

Production-relevant RAG settings:

```dotenv
LLM_PROVIDER=gemini
GEMINI_PROJECT=bac-exercise-generator-prod
GEMINI_LOCATION=europe-west1
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MAX_OUTPUT_TOKENS=8192
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=768
PINECONE_INDEX_NAME=bac-exercises-rag
PINECONE_NAMESPACE=bac-exercises
RAG_ENABLED=true
RAG_FAIL_OPEN=true
RERANKER_ENABLED=false
CODE_RUNNER_PROVIDER=sandbox
RATE_LIMITER_PROVIDER=redis
```

`DATABASE_URL` and `PINECONE_API_KEY` are injected from Secret Manager. Secret
values and corpus text are not written to application logs.

## Quality gates and deployment

```bash
python -m compileall -q src scripts
mypy src tests
ruff check src tests alembic scripts
python -m pytest
```

On pushes to `main`, GitHub Actions runs migrations and the full Python quality
gate, builds an immutable SHA-tagged image, updates and executes the Cloud Run
migration job, then deploys the backend with the gen2 execution environment,
VPC access, Redis, production CORS, Secret Manager, and `sandboxLauncher`.

## Project structure

```text
src/bac_generator/
  ai/                 Gemini, embeddings, retrieval context and reranker
  ingestion/          deterministic PDF classification and exercise parsing
  evaluation/rag/     golden-set metrics, evaluator and reports
  api/                authenticated FastAPI routes and dependencies
  services/           generation, novelty, validation and execution flow
  repositories/       PostgreSQL and Pinecone boundaries
scripts/              corpus build/ingest and RAG validation commands
data/rag/              source corpus, production documents and evaluations
tests/                 unit and integration tests
frontend/              Next.js client
alembic/               database migrations
```

## License

This project is licensed under the MIT License. See `LICENSE` for details.

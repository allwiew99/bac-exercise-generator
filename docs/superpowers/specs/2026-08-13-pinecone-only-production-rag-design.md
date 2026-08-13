# Pinecone-Only Production RAG Design

## Purpose

Make Pinecone ordering the default production behavior while retaining the
Discovery Engine reranker for opt-in experiments. Move RAG client construction
behind a lazy provider so unrelated exercise reads do not initialize Vertex,
Pinecone, or Discovery Engine, and so initialization failures participate in
the existing fail-open policy.

## Configuration

`Settings.reranker_enabled` defaults to `False`, and `.env.example` documents
`RERANKER_ENABLED=false`. Experiments can explicitly set it to `true`. The
reranker implementation, Google dependency, evaluation package, golden set,
and evaluation report remain unchanged and available.

## Runtime components

A focused `RagContextProvider` under `services/` receives:

- a lazy factory for `RetrievalService`;
- a lazy factory for `Reranker`;
- a `ContextBuilder`;
- explicit `rag_enabled`, `reranker_enabled`, and `rag_fail_open` values.

The provider exposes one asynchronous context-building operation. It does not
construct an embedding client, Pinecone repository, or Discovery Engine client
until generation actually requests RAG context.

`ExerciseService` depends on a small provider protocol instead of concrete
retrieval, reranker, and context-builder dependencies. It constructs the same
semantic query and requests context from the provider before building the LLM
prompt. Its retry, validation, and persistence behavior does not change.

## Data flow

When RAG is disabled, the provider returns empty context without invoking any
factory.

When RAG is enabled and reranking is disabled:

1. Lazily construct `RetrievalService`.
2. Retrieve the Pinecone candidates.
3. Pass those candidates to `ContextBuilder` in their original order.
4. `ContextBuilder` selects its configured top five without changing order.
5. Never construct or call `Reranker`.

When both RAG and reranking are enabled:

1. Retrieve the same Pinecone candidates.
2. Lazily construct and call `Reranker`.
3. Pass its result to `ContextBuilder`.

This retains opt-in experimental behavior without making it the production
default.

## Dependency construction

The FastAPI `get_exercise_service` dependency receives only the lightweight
RAG provider. The provider stores factory callables; its creation has no cloud
client side effects. Consequently, list/get endpoints can continue using
`ExerciseService` without constructing Vertex, Pinecone, or Discovery Engine.

The concrete retrieval and reranker factory functions remain independently
callable and are invoked only from the provider's generation-time operation.

## Failure behavior

The provider places external dependency initialization, retrieval, optional
reranking, and context construction inside one scoped error boundary.

- With `rag_fail_open=True`, a failure is logged with traceback and the provider
  returns empty context, so exercise generation proceeds without RAG.
- With `rag_fail_open=False`, the original exception is re-raised.

This is targeted handling around the optional RAG subsystem, not broad route or
application exception swallowing. LLM, validation, database, and unrelated
errors retain their existing behavior.

## Tests

Tests prove observable behavior at the provider/service/route boundaries:

- disabled reranking never invokes the reranker factory or external call;
- Pinecone order reaches `ContextBuilder` unchanged and only its top results
  enter the prompt;
- enabled reranking still invokes the experimental path;
- RAG initialization and retrieval failures fail open or closed according to
  configuration;
- unrelated GET/list endpoints succeed even when all external RAG factories
  would raise if constructed;
- route-level generation survives a lazy RAG initialization failure when
  fail-open is enabled;
- configuration defaults reranking to disabled.

External APIs remain replaced by strict fakes in tests. The final gate runs
`py_compile`, strict `mypy`, `ruff`, focused RAG tests, and the complete pytest
suite. No deployment is performed.

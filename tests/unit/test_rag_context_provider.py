import pytest

from bac_generator.schemas.retrieval import RetrievedChunk
from bac_generator.services.rag_context_provider import RagContextProvider


def _chunks(count: int = 7) -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            id=f"chunk-{index}",
            text=f"Content {index}",
            source="subject.pdf",
            topic="arrays",
            year=2020,
            bac_section="subiectul_II",
            score=1.0 - index / 10,
        )
        for index in range(1, count + 1)
    ]


class FakeRetrievalService:
    def __init__(
        self,
        chunks: list[RetrievedChunk],
        error: Exception | None = None,
    ) -> None:
        self.chunks = chunks
        self.error = error
        self.calls: list[tuple[str, str | None, str | None, int | None]] = []

    async def retrieve(
        self,
        query: str,
        topic: str | None = None,
        difficulty: str | None = None,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        self.calls.append((query, topic, difficulty, top_k))
        if self.error is not None:
            raise self.error
        return self.chunks


class FakeReranker:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self.chunks = chunks
        self.calls: list[tuple[str, list[RetrievedChunk]]] = []

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        self.calls.append((query, chunks))
        return self.chunks


class RecordingContextBuilder:
    def __init__(self) -> None:
        self.calls: list[tuple[list[RetrievedChunk], int]] = []

    def build(
        self,
        chunks: list[RetrievedChunk],
        max_chunks: int = 5,
    ) -> str:
        self.calls.append((chunks, max_chunks))
        return ",".join(chunk.id for chunk in chunks[:max_chunks])


async def test_disabled_rag_does_not_construct_external_dependencies() -> None:
    def forbidden_factory() -> FakeRetrievalService:
        raise AssertionError("retrieval factory must not be called")

    context_builder = RecordingContextBuilder()
    provider = RagContextProvider(
        retrieval_service_factory=forbidden_factory,
        reranker_factory=None,
        context_builder=context_builder,
        rag_enabled=False,
        reranker_enabled=False,
        rag_fail_open=True,
    )

    context = await provider.get_context(
        query="array query",
        topic="arrays",
        difficulty="medium",
    )

    assert context.text == ""
    assert context.chunks == []
    assert context_builder.calls == []


async def test_disabled_reranker_preserves_pinecone_order_for_context() -> None:
    candidates = _chunks()
    retrieval = FakeRetrievalService(candidates)

    def forbidden_reranker_factory() -> FakeReranker:
        raise AssertionError("Discovery Engine must not be constructed")

    context_builder = RecordingContextBuilder()
    provider = RagContextProvider(
        retrieval_service_factory=lambda: retrieval,
        reranker_factory=forbidden_reranker_factory,
        context_builder=context_builder,
        rag_enabled=True,
        reranker_enabled=False,
        rag_fail_open=False,
    )

    context = await provider.get_context(
        query="array query",
        topic="arrays",
        difficulty="medium",
    )

    assert retrieval.calls == [("array query", "arrays", "medium", None)]
    assert context_builder.calls == [(candidates, 5)]
    assert context.text == "chunk-1,chunk-2,chunk-3,chunk-4,chunk-5"
    assert context.chunks == candidates


async def test_enabled_reranker_remains_available_for_experiments() -> None:
    candidates = _chunks()
    reranked = list(reversed(candidates[:5]))
    retrieval = FakeRetrievalService(candidates)
    reranker = FakeReranker(reranked)
    context_builder = RecordingContextBuilder()
    provider = RagContextProvider(
        retrieval_service_factory=lambda: retrieval,
        reranker_factory=lambda: reranker,
        context_builder=context_builder,
        rag_enabled=True,
        reranker_enabled=True,
        rag_fail_open=False,
    )

    context = await provider.get_context(
        query="array query",
        topic="arrays",
        difficulty="medium",
    )

    assert reranker.calls == [("array query", candidates)]
    assert context_builder.calls == [(reranked, 5)]
    assert context.text == "chunk-5,chunk-4,chunk-3,chunk-2,chunk-1"
    assert context.chunks == reranked


@pytest.mark.parametrize("failure_stage", ["initialization", "retrieval"])
async def test_rag_fail_open_covers_initialization_and_retrieval(
    failure_stage: str,
) -> None:
    if failure_stage == "initialization":
        def retrieval_factory() -> FakeRetrievalService:
            raise RuntimeError("Pinecone initialization failed")
    else:
        retrieval = FakeRetrievalService(
            [],
            error=RuntimeError("Pinecone retrieval failed"),
        )

        def retrieval_factory() -> FakeRetrievalService:
            return retrieval

    context_builder = RecordingContextBuilder()
    provider = RagContextProvider(
        retrieval_service_factory=retrieval_factory,
        reranker_factory=None,
        context_builder=context_builder,
        rag_enabled=True,
        reranker_enabled=False,
        rag_fail_open=True,
    )

    context = await provider.get_context(
        query="array query",
        topic="arrays",
        difficulty="medium",
    )

    assert context.text == ""
    assert context.chunks == []
    assert context_builder.calls == []


async def test_rag_fail_closed_reraises_initialization_failure() -> None:
    def retrieval_factory() -> FakeRetrievalService:
        raise RuntimeError("Pinecone initialization failed")

    provider = RagContextProvider(
        retrieval_service_factory=retrieval_factory,
        reranker_factory=None,
        context_builder=RecordingContextBuilder(),
        rag_enabled=True,
        reranker_enabled=False,
        rag_fail_open=False,
    )

    with pytest.raises(RuntimeError, match="Pinecone initialization failed"):
        await provider.get_context(
            query="array query",
            topic="arrays",
            difficulty="medium",
        )

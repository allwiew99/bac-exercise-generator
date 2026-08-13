import logging

import pytest

from bac_generator.repositories.vector_repository_protocol import VectorMetadata
from bac_generator.schemas.retrieval import RetrievedChunk
from bac_generator.services.retrieval_service import RetrievalService


def _chunk(chunk_id: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        id=chunk_id,
        text=f"Content for {chunk_id}",
        source="source.pdf",
        topic="arrays",
        year=2020,
        bac_section="subiectul_II",
        exercise_type="open_response",
        difficulty=None,
        score=score,
    )


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.vector = [0.1, 0.2, 0.3]

    def embed_text(self, text: str) -> list[float]:
        self.calls.append(text)
        return self.vector

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]


class FakeVectorRepository:
    def __init__(self, responses: list[list[RetrievedChunk]]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[list[float], int, dict[str, str | int] | None]] = []

    def query(
        self,
        vector: list[float],
        top_k: int,
        filters: dict[str, str | int] | None = None,
    ) -> list[RetrievedChunk]:
        self.calls.append((vector, top_k, filters))
        return self.responses.pop(0)

    def upsert(
        self,
        vectors: list[tuple[str, list[float], VectorMetadata]],
    ) -> None:
        raise AssertionError("retrieval must never upsert vectors")


async def test_filtered_retrieval_with_enough_results_does_not_fallback() -> None:
    embedding_client = FakeEmbeddingClient()
    expected = [_chunk("a", 0.9), _chunk("b", 0.8), _chunk("c", 0.7)]
    repository = FakeVectorRepository([expected])
    service = RetrievalService(embedding_client, repository)

    result = await service.retrieve(
        "  vector exercise  ",
        topic="arrays",
        difficulty="medium",
        top_k=3,
    )

    assert result == expected
    assert embedding_client.calls == ["vector exercise"]
    assert repository.calls == [
        (embedding_client.vector, 3, {"topic": "arrays", "difficulty": "medium"})
    ]


async def test_sparse_filtered_retrieval_falls_back_and_merges_results(
    caplog: pytest.LogCaptureFixture,
) -> None:
    embedding_client = FakeEmbeddingClient()
    filtered = [_chunk("duplicate", 0.8)]
    unfiltered = [
        _chunk("duplicate", 0.9),
        _chunk("second", 0.7),
        _chunk("third", 0.6),
        _chunk("fourth", 0.5),
    ]
    repository = FakeVectorRepository([filtered, unfiltered])
    service = RetrievalService(embedding_client, repository)

    with caplog.at_level(logging.WARNING):
        result = await service.retrieve("vector exercise", topic="arrays", top_k=3)

    assert [chunk.id for chunk in result] == ["duplicate", "second", "third"]
    assert result[0].score == 0.9
    assert len(result) == 3
    assert embedding_client.calls == ["vector exercise"]
    assert len(repository.calls) == 2
    assert repository.calls[0] == (embedding_client.vector, 3, {"topic": "arrays"})
    assert repository.calls[1] == (embedding_client.vector, 3, None)
    assert repository.calls[0][0] is repository.calls[1][0]
    assert (
        "Filtered RAG retrieval returned 1/3 candidates; falling back to semantic "
        "retrieval without metadata filters."
    ) in caplog.messages


async def test_merge_retains_filtered_chunk_when_it_has_best_score() -> None:
    filtered = [_chunk("duplicate", 0.95)]
    unfiltered = [_chunk("duplicate", 0.7), _chunk("second", 0.6)]
    service = RetrievalService(
        FakeEmbeddingClient(),
        FakeVectorRepository([filtered, unfiltered]),
    )

    result = await service.retrieve("vector exercise", difficulty="medium", top_k=2)

    assert [chunk.id for chunk in result] == ["duplicate", "second"]
    assert result[0].score == 0.95


async def test_unfiltered_retrieval_does_not_query_twice_when_sparse() -> None:
    embedding_client = FakeEmbeddingClient()
    repository = FakeVectorRepository([[_chunk("only", 0.5)]])
    service = RetrievalService(embedding_client, repository)

    result = await service.retrieve("vector exercise", top_k=3)

    assert [chunk.id for chunk in result] == ["only"]
    assert embedding_client.calls == ["vector exercise"]
    assert repository.calls == [(embedding_client.vector, 3, None)]


async def test_empty_query_is_rejected_before_embedding() -> None:
    embedding_client = FakeEmbeddingClient()
    repository = FakeVectorRepository([])
    service = RetrievalService(embedding_client, repository)

    with pytest.raises(ValueError, match="cannot be empty"):
        await service.retrieve("  \n  ")

    assert embedding_client.calls == []
    assert repository.calls == []

@pytest.mark.parametrize("top_k", [0, -1])
async def test_non_positive_top_k_is_rejected_before_embedding(top_k: int) -> None:
    embedding_client = FakeEmbeddingClient()
    repository = FakeVectorRepository([])
    service = RetrievalService(embedding_client, repository)

    with pytest.raises(ValueError, match="greater than zero"):
        await service.retrieve("vector exercise", top_k=top_k)

    assert embedding_client.calls == []
    assert repository.calls == []

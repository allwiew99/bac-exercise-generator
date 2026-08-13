from collections.abc import Iterator

from bac_generator.evaluation.rag.evaluator import RagRetrievalEvaluator
from bac_generator.evaluation.rag.models import (
    GoldenDataset,
    GoldenQuery,
    RelevanceGroup,
)
from bac_generator.schemas.retrieval import RetrievedChunk


def _chunk(document_id: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        id=document_id,
        text=f"Content for {document_id}",
        source="subject.pdf",
        topic="arrays",
        year=2020,
        bac_section="subiectul_II",
        score=score,
    )


def _query(query_id: str = "query-one") -> GoldenQuery:
    return GoldenQuery(
        id=query_id,
        text=f"Text for {query_id}",
        topic="binary search",
        topic_filter="arrays",
        relevance_groups=[
            RelevanceGroup(
                id="equivalent",
                grade=3,
                document_ids=["relevant-mi", "relevant-sn"],
                rationale="Equivalent profile variants.",
            ),
            RelevanceGroup(
                id="distinct",
                grade=2,
                document_ids=["relevant-other"],
                rationale="A distinct relevant exercise.",
            ),
        ],
    )


class FakeRetrievalService:
    def __init__(self, candidates: list[RetrievedChunk]) -> None:
        self.candidates = candidates
        self.calls: list[tuple[str, str | None, int]] = []

    async def retrieve(
        self,
        query: str,
        topic: str | None = None,
        difficulty: str | None = None,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        assert difficulty is None
        assert top_k is not None
        self.calls.append((query, topic, top_k))
        return self.candidates


class FakeReranker:
    def __init__(
        self,
        reranked: list[RetrievedChunk],
        expected_candidates: list[RetrievedChunk],
    ) -> None:
        self.reranked = reranked
        self.expected_candidates = expected_candidates
        self.received_same_list = False

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        assert query == "Text for query-one"
        self.received_same_list = chunks is self.expected_candidates
        return self.reranked


class SequenceClock:
    def __init__(self, *values: float) -> None:
        self._values: Iterator[float] = iter(values)

    def __call__(self) -> float:
        return next(self._values)


async def test_evaluator_uses_one_top8_candidate_set_for_both_rankings() -> None:
    candidates = [
        _chunk("relevant-mi", 0.9),
        _chunk("relevant-sn", 0.8),
        _chunk("irrelevant-1", 0.7),
        _chunk("irrelevant-2", 0.6),
        _chunk("irrelevant-3", 0.5),
        _chunk("relevant-other", 0.4),
        _chunk("irrelevant-4", 0.3),
        _chunk("irrelevant-5", 0.2),
    ]
    reranked = [
        candidates[5].model_copy(update={"score": 0.95}),
        candidates[0].model_copy(update={"score": 0.90}),
        candidates[1].model_copy(update={"score": 0.85}),
        candidates[2].model_copy(update={"score": 0.20}),
        candidates[3].model_copy(update={"score": 0.10}),
    ]
    retrieval = FakeRetrievalService(candidates)
    reranker = FakeReranker(reranked, candidates)
    evaluator = RagRetrievalEvaluator(
        retrieval_service=retrieval,
        reranker=reranker,
        clock=SequenceClock(10.0, 10.125, 20.0, 20.5),
    )

    run = await evaluator.evaluate(GoldenDataset(version=1, queries=[_query()]))

    assert retrieval.calls == [("Text for query-one", "arrays", 8)]
    assert reranker.received_same_list is True
    assert run.failures == []
    assert len(run.results) == 1
    result = run.results[0]
    assert [item.id for item in result.baseline_top8] == [
        chunk.id for chunk in candidates
    ]
    assert [item.id for item in result.baseline_top5] == [
        chunk.id for chunk in candidates[:5]
    ]
    assert [item.id for item in result.reranked_top5] == [
        chunk.id for chunk in reranked
    ]
    assert result.baseline_at5.recall == 0.5
    assert result.baseline_at8.recall == 1.0
    assert result.baseline_at5.duplicate_group_hits == 1
    assert result.reranked_at5.recall == 1.0
    assert result.outcome == "improved"
    assert result.retrieval_latency_ms == 125.0
    assert result.reranker_latency_ms == 500.0
    assert result.combined_latency_ms == 625.0


class FailingRetrievalService:
    async def retrieve(
        self,
        query: str,
        topic: str | None = None,
        difficulty: str | None = None,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        del topic, difficulty, top_k
        if query == "Text for retrieval-failure":
            raise PermissionError("Pinecone denied access")
        return [_chunk("relevant-mi", 0.9)]


class SelectivelyFailingReranker:
    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        if query == "Text for reranking-failure":
            raise RuntimeError("Discovery Engine unavailable")
        return chunks


async def test_evaluator_records_stage_failures_and_continues() -> None:
    dataset = GoldenDataset(
        version=1,
        queries=[
            _query("retrieval-failure"),
            _query("reranking-failure"),
            _query("successful-query"),
        ],
    )
    evaluator = RagRetrievalEvaluator(
        retrieval_service=FailingRetrievalService(),
        reranker=SelectivelyFailingReranker(),
        clock=SequenceClock(
            0.0,
            0.1,
            1.0,
            1.1,
            2.0,
            2.1,
            3.0,
            3.1,
            4.0,
            4.1,
        ),
    )

    run = await evaluator.evaluate(dataset)

    assert [result.query_id for result in run.results] == ["successful-query"]
    assert [(failure.query_id, failure.stage) for failure in run.failures] == [
        ("retrieval-failure", "retrieval"),
        ("reranking-failure", "reranking"),
    ]
    assert run.failures[0].error_type == "PermissionError"
    assert run.failures[1].message == "Discovery Engine unavailable"

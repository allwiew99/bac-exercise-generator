from collections.abc import Callable
from typing import Protocol

from bac_generator.evaluation.rag.aggregator import classify_outcome
from bac_generator.evaluation.rag.metrics import evaluate_ranking
from bac_generator.evaluation.rag.models import (
    EvaluationFailure,
    EvaluationRun,
    GoldenDataset,
    GoldenQuery,
    QueryEvaluation,
    RankedResult,
)
from bac_generator.schemas.retrieval import RetrievedChunk

Clock = Callable[[], float]


class RetrievalServiceProtocol(Protocol):
    async def retrieve(
        self,
        query: str,
        topic: str | None = None,
        difficulty: str | None = None,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        ...


class RerankerProtocol(Protocol):
    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        ...


class RagRetrievalEvaluator:
    def __init__(
        self,
        retrieval_service: RetrievalServiceProtocol,
        reranker: RerankerProtocol,
        clock: Clock,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.reranker = reranker
        self.clock = clock

    async def evaluate(self, dataset: GoldenDataset) -> EvaluationRun:
        results: list[QueryEvaluation] = []
        failures: list[EvaluationFailure] = []

        for query in dataset.queries:
            result, failure = await self._evaluate_query(query)
            if result is not None:
                results.append(result)
            if failure is not None:
                failures.append(failure)

        return EvaluationRun(results=results, failures=failures)

    async def _evaluate_query(
        self,
        query: GoldenQuery,
    ) -> tuple[QueryEvaluation | None, EvaluationFailure | None]:
        retrieval_started = self.clock()
        try:
            candidates = await self.retrieval_service.retrieve(
                query.text,
                topic=query.topic_filter,
                top_k=8,
            )
        except Exception as error:
            self.clock()
            return None, _failure(query.id, "retrieval", error)
        retrieval_finished = self.clock()

        reranking_started = self.clock()
        try:
            reranked = await self.reranker.rerank(query.text, candidates)
        except Exception as error:
            self.clock()
            return None, _failure(query.id, "reranking", error)
        reranking_finished = self.clock()

        baseline_ids = [chunk.id for chunk in candidates]
        reranked_ids = [chunk.id for chunk in reranked]
        baseline_at5 = evaluate_ranking(
            baseline_ids,
            query.relevance_groups,
            cutoff=5,
        )
        baseline_at8 = evaluate_ranking(
            baseline_ids,
            query.relevance_groups,
            cutoff=8,
        )
        reranked_at5 = evaluate_ranking(
            reranked_ids,
            query.relevance_groups,
            cutoff=5,
        )
        retrieval_latency_ms = (retrieval_finished - retrieval_started) * 1000
        reranker_latency_ms = (reranking_finished - reranking_started) * 1000

        return (
            QueryEvaluation(
                query_id=query.id,
                query_text=query.text,
                topic=query.topic,
                topic_filter=query.topic_filter,
                baseline_top8=_ranked_results(candidates[:8]),
                baseline_top5=_ranked_results(candidates[:5]),
                reranked_top5=_ranked_results(reranked[:5]),
                baseline_at5=baseline_at5,
                baseline_at8=baseline_at8,
                reranked_at5=reranked_at5,
                outcome=classify_outcome(
                    baseline_at5.ndcg,
                    reranked_at5.ndcg,
                ),
                retrieval_latency_ms=retrieval_latency_ms,
                reranker_latency_ms=reranker_latency_ms,
                combined_latency_ms=(retrieval_latency_ms + reranker_latency_ms),
            ),
            None,
        )


def _ranked_results(chunks: list[RetrievedChunk]) -> list[RankedResult]:
    return [
        RankedResult(
            rank=rank,
            id=chunk.id,
            score=chunk.score,
            topic=chunk.topic,
            source=chunk.source,
            year=chunk.year,
            bac_section=chunk.bac_section,
        )
        for rank, chunk in enumerate(chunks, start=1)
    ]


def _failure(
    query_id: str,
    stage: str,
    error: Exception,
) -> EvaluationFailure:
    if stage == "retrieval":
        return EvaluationFailure(
            query_id=query_id,
            stage="retrieval",
            error_type=type(error).__name__,
            message=str(error),
        )
    return EvaluationFailure(
        query_id=query_id,
        stage="reranking",
        error_type=type(error).__name__,
        message=str(error),
    )

import math
import statistics

from bac_generator.evaluation.rag.models import (
    EvaluationFailure,
    EvaluationReport,
    LatencyAggregate,
    LatencyStatistics,
    MetricAggregate,
    OutcomeCounts,
    QueryEvaluation,
    QueryOutcome,
    TopicEvaluationSummary,
)

NDCG_TOLERANCE = 1e-9


def classify_outcome(
    baseline_ndcg: float,
    reranked_ndcg: float,
) -> QueryOutcome:
    delta = reranked_ndcg - baseline_ndcg
    if delta > NDCG_TOLERANCE:
        return "improved"
    if delta < -NDCG_TOLERANCE:
        return "degraded"
    return "unchanged"


def build_evaluation_report(
    *,
    total_queries: int,
    results: list[QueryEvaluation],
    failures: list[EvaluationFailure],
    generated_at: str,
    reranker_model: str,
    ranking_config: str,
) -> EvaluationReport:
    sorted_results = sorted(results, key=lambda result: result.query_id)
    sorted_failures = sorted(failures, key=lambda failure: failure.query_id)
    successful_queries = len(sorted_results)
    failed_queries = len(sorted_failures)

    topics = sorted({result.topic for result in sorted_results})
    per_topic = {
        topic: _topic_summary(
            [result for result in sorted_results if result.topic == topic]
        )
        for topic in topics
    }

    return EvaluationReport(
        generated_at=generated_at,
        reranker_model=reranker_model,
        ranking_config=ranking_config,
        total_queries=total_queries,
        successful_queries=successful_queries,
        failed_queries=failed_queries,
        successful_query_ratio=_ratio(successful_queries, total_queries),
        failed_query_ratio=_ratio(failed_queries, total_queries),
        baseline=_metric_aggregate(sorted_results, reranked=False),
        reranked=_metric_aggregate(sorted_results, reranked=True),
        outcomes=_outcome_counts(sorted_results),
        latency=_latency_aggregate(sorted_results),
        per_topic=per_topic,
        query_results=sorted_results,
        failures=sorted_failures,
    )


def _topic_summary(results: list[QueryEvaluation]) -> TopicEvaluationSummary:
    return TopicEvaluationSummary(
        query_count=len(results),
        baseline=_metric_aggregate(results, reranked=False),
        reranked=_metric_aggregate(results, reranked=True),
        outcomes=_outcome_counts(results),
    )


def _metric_aggregate(
    results: list[QueryEvaluation],
    *,
    reranked: bool,
) -> MetricAggregate:
    if not results:
        return MetricAggregate(
            recall_at5=0.0,
            mrr_at5=0.0,
            ndcg_at5=0.0,
            recall_at8=None if reranked else 0.0,
        )

    metrics = [
        result.reranked_at5 if reranked else result.baseline_at5
        for result in results
    ]
    return MetricAggregate(
        recall_at5=statistics.fmean(metric.recall for metric in metrics),
        mrr_at5=statistics.fmean(metric.mrr for metric in metrics),
        ndcg_at5=statistics.fmean(metric.ndcg for metric in metrics),
        recall_at8=(
            None
            if reranked
            else statistics.fmean(
                result.baseline_at8.recall for result in results
            )
        ),
    )


def _outcome_counts(results: list[QueryEvaluation]) -> OutcomeCounts:
    return OutcomeCounts(
        improved=sum(result.outcome == "improved" for result in results),
        unchanged=sum(result.outcome == "unchanged" for result in results),
        degraded=sum(result.outcome == "degraded" for result in results),
    )


def _latency_aggregate(results: list[QueryEvaluation]) -> LatencyAggregate:
    return LatencyAggregate(
        retrieval=_latency_statistics(
            [result.retrieval_latency_ms for result in results]
        ),
        reranker=_latency_statistics(
            [result.reranker_latency_ms for result in results]
        ),
        combined=_latency_statistics(
            [result.combined_latency_ms for result in results]
        ),
    )


def _latency_statistics(values: list[float]) -> LatencyStatistics:
    if not values:
        return LatencyStatistics(
            count=0,
            mean_ms=0.0,
            median_ms=0.0,
            p95_ms=0.0,
            min_ms=0.0,
            max_ms=0.0,
        )

    ordered = sorted(values)
    p95_index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return LatencyStatistics(
        count=len(ordered),
        mean_ms=statistics.fmean(ordered),
        median_ms=statistics.median(ordered),
        p95_ms=ordered[p95_index],
        min_ms=ordered[0],
        max_ms=ordered[-1],
    )


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0

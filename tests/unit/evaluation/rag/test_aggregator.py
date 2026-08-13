from bac_generator.evaluation.rag.aggregator import (
    build_evaluation_report,
    classify_outcome,
)
from bac_generator.evaluation.rag.models import (
    EvaluationFailure,
    QueryEvaluation,
    RankedResult,
    RankingMetrics,
)


def _metrics(
    recall: float,
    mrr: float,
    ndcg: float,
) -> RankingMetrics:
    return RankingMetrics(
        recall=recall,
        mrr=mrr,
        ndcg=ndcg,
        matched_group_ids=[],
        relevant_groups=2,
        raw_relevant_document_hits=0,
        duplicate_group_hits=0,
    )


def _result(
    query_id: str,
    topic: str,
    baseline_ndcg: float,
    reranked_ndcg: float,
    retrieval_ms: float,
    reranker_ms: float,
) -> QueryEvaluation:
    ranked = RankedResult(
        rank=1,
        id=f"{query_id}-document",
        score=0.8,
        topic=topic,
        source="subject.pdf",
    )
    return QueryEvaluation(
        query_id=query_id,
        query_text=f"Query {query_id}",
        topic=topic,
        topic_filter=topic,
        baseline_top8=[ranked],
        baseline_top5=[ranked],
        reranked_top5=[ranked],
        baseline_at5=_metrics(0.5, 1.0, baseline_ndcg),
        baseline_at8=_metrics(1.0, 1.0, baseline_ndcg),
        reranked_at5=_metrics(0.5, 1.0, reranked_ndcg),
        outcome=classify_outcome(baseline_ndcg, reranked_ndcg),
        retrieval_latency_ms=retrieval_ms,
        reranker_latency_ms=reranker_ms,
        combined_latency_ms=retrieval_ms + reranker_ms,
    )


def test_classify_outcome_uses_ndcg_and_tolerance() -> None:
    assert classify_outcome(0.4, 0.6) == "improved"
    assert classify_outcome(0.6, 0.4) == "degraded"
    assert classify_outcome(0.5, 0.5 + 1e-10) == "unchanged"


def test_report_aggregates_metrics_topics_outcomes_latency_and_failures() -> None:
    results = [
        _result("z-query", "files", 0.2, 0.6, 100.0, 300.0),
        _result("a-query", "files", 0.8, 0.5, 200.0, 500.0),
        _result("m-query", "graphs", 0.7, 0.7, 300.0, 700.0),
    ]
    failures = [
        EvaluationFailure(
            query_id="failed-query",
            stage="reranking",
            error_type="RuntimeError",
            message="service unavailable",
        )
    ]

    report = build_evaluation_report(
        total_queries=4,
        results=results,
        failures=failures,
        generated_at="2026-08-13T12:00:00Z",
        reranker_model="test-ranker",
        ranking_config="projects/test/rankingConfigs/default",
    )

    assert report.successful_queries == 3
    assert report.failed_queries == 1
    assert report.successful_query_ratio == 0.75
    assert report.failed_query_ratio == 0.25
    assert report.outcomes.model_dump() == {
        "improved": 1,
        "unchanged": 1,
        "degraded": 1,
    }
    assert report.baseline.recall_at5 == 0.5
    assert report.baseline.mrr_at5 == 1.0
    assert report.baseline.ndcg_at5 == (0.2 + 0.8 + 0.7) / 3
    assert report.baseline.recall_at8 == 1.0
    assert report.reranked.ndcg_at5 == (0.6 + 0.5 + 0.7) / 3
    assert report.reranked.recall_at8 is None
    assert list(report.per_topic) == ["files", "graphs"]
    assert report.per_topic["files"].query_count == 2
    assert report.per_topic["files"].outcomes.improved == 1
    assert report.per_topic["files"].outcomes.degraded == 1
    assert report.latency.retrieval.mean_ms == 200.0
    assert report.latency.retrieval.median_ms == 200.0
    assert report.latency.retrieval.p95_ms == 300.0
    assert report.latency.reranker.mean_ms == 500.0
    assert report.latency.combined.mean_ms == 700.0
    assert [result.query_id for result in report.query_results] == [
        "a-query",
        "m-query",
        "z-query",
    ]


def test_report_aggregation_is_deterministic_for_input_order() -> None:
    first = _result("b", "trees", 0.4, 0.6, 10.0, 20.0)
    second = _result("a", "arrays", 0.7, 0.7, 20.0, 30.0)

    report_one = build_evaluation_report(
        total_queries=2,
        results=[first, second],
        failures=[],
        generated_at="2026-08-13T12:00:00Z",
        reranker_model="test-ranker",
        ranking_config="config",
    )
    report_two = build_evaluation_report(
        total_queries=2,
        results=[second, first],
        failures=[],
        generated_at="2026-08-13T12:00:00Z",
        reranker_model="test-ranker",
        ranking_config="config",
    )

    assert report_one.model_dump() == report_two.model_dump()

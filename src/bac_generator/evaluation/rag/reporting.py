from pathlib import Path

from bac_generator.evaluation.rag.models import EvaluationReport


def write_report(report: EvaluationReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        report.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )


def format_console_summary(report: EvaluationReport) -> str:
    lines = [
        "RAG retrieval evaluation",
        (
            f"Successful queries: {report.successful_queries}/"
            f"{report.total_queries} ({report.successful_query_ratio:.1%})"
        ),
        (
            f"Failed queries: {report.failed_queries}/"
            f"{report.total_queries} ({report.failed_query_ratio:.1%})"
        ),
        (
            "Baseline Pinecone: "
            f"Recall@5={report.baseline.recall_at5:.4f}, "
            f"MRR@5={report.baseline.mrr_at5:.4f}, "
            f"nDCG@5={report.baseline.ndcg_at5:.4f}, "
            f"Recall@8={(report.baseline.recall_at8 or 0.0):.4f}"
        ),
        (
            "Discovery Engine reranked: "
            f"Recall@5={report.reranked.recall_at5:.4f}, "
            f"MRR@5={report.reranked.mrr_at5:.4f}, "
            f"nDCG@5={report.reranked.ndcg_at5:.4f}"
        ),
        (
            "Outcomes: "
            f"improved={report.outcomes.improved}, "
            f"unchanged={report.outcomes.unchanged}, "
            f"degraded={report.outcomes.degraded}"
        ),
        (
            "Latency mean/p95 (ms): "
            f"retrieval={report.latency.retrieval.mean_ms:.1f}/"
            f"{report.latency.retrieval.p95_ms:.1f}, "
            f"reranker={report.latency.reranker.mean_ms:.1f}/"
            f"{report.latency.reranker.p95_ms:.1f}, "
            f"combined={report.latency.combined.mean_ms:.1f}/"
            f"{report.latency.combined.p95_ms:.1f}"
        ),
        "Per-topic metrics:",
    ]

    for topic, summary in report.per_topic.items():
        lines.append(
            f"  {topic} ({summary.query_count}): "
            f"baseline R@5={summary.baseline.recall_at5:.4f}, "
            f"MRR={summary.baseline.mrr_at5:.4f}, "
            f"nDCG={summary.baseline.ndcg_at5:.4f}, "
            f"R@8={(summary.baseline.recall_at8 or 0.0):.4f}; "
            f"reranked R@5={summary.reranked.recall_at5:.4f}, "
            f"MRR={summary.reranked.mrr_at5:.4f}, "
            f"nDCG={summary.reranked.ndcg_at5:.4f}; "
            f"I/U/D={summary.outcomes.improved}/"
            f"{summary.outcomes.unchanged}/{summary.outcomes.degraded}"
        )

    if report.failures:
        lines.append("Failures:")
        for failure in report.failures:
            lines.append(
                f"  {failure.query_id} [{failure.stage}] "
                f"{failure.error_type}: {failure.message}"
            )

    return "\n".join(lines)

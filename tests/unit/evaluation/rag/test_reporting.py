import json
from pathlib import Path

from bac_generator.evaluation.rag.aggregator import build_evaluation_report
from bac_generator.evaluation.rag.models import EvaluationFailure
from bac_generator.evaluation.rag.reporting import (
    format_console_summary,
    write_report,
)


def test_console_summary_makes_success_and_failure_ratios_visible() -> None:
    report = build_evaluation_report(
        total_queries=2,
        results=[],
        failures=[
            EvaluationFailure(
                query_id="one",
                stage="retrieval",
                error_type="RuntimeError",
                message="failed",
            ),
            EvaluationFailure(
                query_id="two",
                stage="reranking",
                error_type="RuntimeError",
                message="failed",
            ),
        ],
        generated_at="2026-08-13T12:00:00Z",
        reranker_model="ranker",
        ranking_config="config",
    )

    summary = format_console_summary(report)

    assert "Successful queries: 0/2 (0.0%)" in summary
    assert "Failed queries: 2/2 (100.0%)" in summary
    assert "Baseline Pinecone: Recall@5=0.0000" in summary
    assert "Failures:" in summary
    assert "one [retrieval] RuntimeError: failed" in summary


def test_write_report_serializes_stable_pretty_json(tmp_path: Path) -> None:
    report = build_evaluation_report(
        total_queries=0,
        results=[],
        failures=[],
        generated_at="2026-08-13T12:00:00Z",
        reranker_model="ranker",
        ranking_config="config",
    )
    output_path = tmp_path / "report.json"

    write_report(report, output_path)

    content = output_path.read_text(encoding="utf-8")
    assert content.endswith("\n")
    assert json.loads(content)["successful_queries"] == 0
    assert content == report.model_dump_json(indent=2) + "\n"

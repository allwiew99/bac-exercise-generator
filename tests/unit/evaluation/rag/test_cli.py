import json
from pathlib import Path

from bac_generator.evaluation.rag.cli import run_evaluation
from bac_generator.evaluation.rag.models import (
    EvaluationFailure,
    EvaluationRun,
    GoldenDataset,
)


class FakeEvaluator:
    def __init__(self) -> None:
        self.dataset: GoldenDataset | None = None

    async def evaluate(self, dataset: GoldenDataset) -> EvaluationRun:
        self.dataset = dataset
        return EvaluationRun(
            results=[],
            failures=[
                EvaluationFailure(
                    query_id=dataset.queries[0].id,
                    stage="reranking",
                    error_type="RuntimeError",
                    message="mocked API failure",
                )
            ],
        )


async def test_run_evaluation_validates_data_writes_report_and_flags_failure(
    tmp_path: Path,
) -> None:
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(
        json.dumps(
            [
                {
                    "id": "known-document",
                    "text": "Known exercise",
                    "source": "subject.pdf",
                    "topic": "arrays",
                }
            ]
        ),
        encoding="utf-8",
    )
    dataset_path = tmp_path / "golden.json"
    dataset_path.write_text(
        json.dumps(
            {
                "version": 1,
                "queries": [
                    {
                        "id": "query-one",
                        "text": "Find the exercise",
                        "topic": "arrays",
                        "topic_filter": "arrays",
                        "relevance_groups": [
                            {
                                "id": "target",
                                "grade": 3,
                                "document_ids": ["known-document"],
                                "rationale": "Direct match",
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "report.json"
    evaluator = FakeEvaluator()

    exit_code, report, summary = await run_evaluation(
        evaluator=evaluator,
        dataset_path=dataset_path,
        corpus_path=corpus_path,
        output_path=output_path,
        generated_at="2026-08-13T12:00:00Z",
        reranker_model="mocked-ranker",
        ranking_config="mocked-config",
    )

    assert exit_code == 1
    assert evaluator.dataset is not None
    assert report.successful_queries == 0
    assert report.failed_queries == 1
    assert "Successful queries: 0/1 (0.0%)" in summary
    assert "Failed queries: 1/1 (100.0%)" in summary
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written["failed_queries"] == 1
    assert written["failures"][0]["message"] == "mocked API failure"

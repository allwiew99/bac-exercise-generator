import argparse
import asyncio
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from pydantic import TypeAdapter

from bac_generator.ai.embeddings.vertex_embedding_client import (
    VertexEmbeddingClient,
)
from bac_generator.ai.retrieval.reranker import Reranker
from bac_generator.core.config import settings
from bac_generator.evaluation.rag.aggregator import build_evaluation_report
from bac_generator.evaluation.rag.dataset import load_golden_dataset
from bac_generator.evaluation.rag.evaluator import RagRetrievalEvaluator
from bac_generator.evaluation.rag.models import (
    EvaluationReport,
    EvaluationRun,
    GoldenDataset,
)
from bac_generator.evaluation.rag.reporting import (
    format_console_summary,
    write_report,
)
from bac_generator.repositories.pinecone_repository import PineconeRepository
from bac_generator.schemas.retrieval import RetrievalDocument
from bac_generator.services.retrieval_service import RetrievalService

DEFAULT_DATASET_PATH = Path("data/rag/evaluation/retrieval_golden.json")
DEFAULT_CORPUS_PATH = Path("data/rag/bac_corpus.json")
DEFAULT_OUTPUT_PATH = Path(
    "data/rag/evaluation/retrieval_evaluation_report.json"
)


class EvaluatorProtocol(Protocol):
    async def evaluate(self, dataset: GoldenDataset) -> EvaluationRun:
        ...


async def run_evaluation(
    *,
    evaluator: EvaluatorProtocol,
    dataset_path: Path,
    corpus_path: Path,
    output_path: Path,
    generated_at: str,
    reranker_model: str,
    ranking_config: str,
) -> tuple[int, EvaluationReport, str]:
    corpus_documents = TypeAdapter(list[RetrievalDocument]).validate_json(
        corpus_path.read_text(encoding="utf-8")
    )
    dataset = load_golden_dataset(dataset_path, corpus_documents)
    run = await evaluator.evaluate(dataset)
    report = build_evaluation_report(
        total_queries=len(dataset.queries),
        results=run.results,
        failures=run.failures,
        generated_at=generated_at,
        reranker_model=reranker_model,
        ranking_config=ranking_config,
    )
    write_report(report, output_path)
    summary = format_console_summary(report)
    exit_code = 1 if report.failed_queries else 0
    return exit_code, report, summary


async def async_main(argv: Sequence[str] | None = None) -> int:
    parser = _argument_parser()
    args = parser.parse_args(argv)

    if not settings.reranker_enabled:
        parser.error("Reranker must be enabled for comparative evaluation.")

    retrieval_service = RetrievalService(
        embedding_client=VertexEmbeddingClient(),
        vector_repository=PineconeRepository(),
        default_top_k=8,
    )
    reranker = Reranker(
        project_id=settings.gemini_project,
        model=settings.reranker_model,
        top_n=5,
    )
    evaluator = RagRetrievalEvaluator(
        retrieval_service=retrieval_service,
        reranker=reranker,
        clock=time.perf_counter,
    )
    ranking_config = (
        f"projects/{settings.gemini_project}/locations/global/"
        "rankingConfigs/default_ranking_config"
    )
    exit_code, _, summary = await run_evaluation(
        evaluator=evaluator,
        dataset_path=args.dataset,
        corpus_path=args.corpus,
        output_path=args.output,
        generated_at=_utc_timestamp(),
        reranker_model=settings.reranker_model,
        ranking_config=ranking_config,
    )
    print(summary)
    print(f"Report: {args.output}")
    return exit_code


def main(argv: Sequence[str] | None = None) -> None:
    raise SystemExit(asyncio.run(async_main(argv)))


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare Pinecone retrieval with Discovery Engine reranking "
            "over an auditable golden query set."
        )
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")

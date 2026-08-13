import asyncio
from pathlib import Path

from bac_generator.core.logging_config import configure_logging
from bac_generator.evaluation.rag.generation_e2e import (
    GenerationE2EReport,
    cleanup_validation_rows,
    create_validation_user_id,
    finalize_e2e_report,
    run_e2e_validation,
)

DEFAULT_OUTPUT_PATH = Path(
    "data/rag/evaluation/generation_e2e_report.json"
)


async def main() -> int:
    configure_logging()
    validation_user_id = create_validation_user_id()
    report: GenerationE2EReport | None = None
    try:
        report = await run_e2e_validation(
            validation_user_id=validation_user_id
        )
        _write_report(report)
    finally:
        cleanup = await cleanup_validation_rows(validation_user_id)

    if report is None:
        raise RuntimeError(
            "E2E validation ended before a report was produced. Cleanup result: "
            f"{cleanup.model_dump_json()}"
        )
    report = finalize_e2e_report(report, cleanup)
    _write_report(report)

    _print_summary(report)
    return 0 if report.safe_for_production_deployment else 1


def _write_report(report: GenerationE2EReport) -> None:
    DEFAULT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT_PATH.write_text(
        report.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )


def _print_summary(report: GenerationE2EReport) -> None:
    print(f"E2E cases: {len(report.cases)}")
    print(
        f"Successful cases: {report.successful_cases}/{len(report.cases)}"
    )
    print(f"Failed cases: {report.failed_cases}/{len(report.cases)}")
    print(f"Semantic fallback cases: {report.fallback_cases}")
    print(f"Suspicious novelty cases: {report.suspicious_novelty_cases}")
    print(
        "Discovery Engine used: "
        f"{report.reranker.discovery_engine_used}"
    )
    print(
        "Safe for production deployment: "
        f"{report.safe_for_production_deployment}"
    )
    print(f"Validation user ID: {report.persistence.validation_user_id}")
    print(f"Inserted validation rows: {report.persistence.inserted_count}")
    print(f"Deleted validation rows: {report.persistence.deleted_count}")
    print(f"Remaining validation rows: {report.persistence.remaining_rows}")
    print(f"Deterministic cleanup SQL: {report.persistence.cleanup_sql}")
    print(f"Report: {DEFAULT_OUTPUT_PATH}")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

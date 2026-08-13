import argparse
from collections.abc import Sequence
from pathlib import Path

from bac_generator.ingestion.corpus_builder import build_corpus, write_preview

DEFAULT_RAW_DIR = Path("data/rag/raw")
DEFAULT_OUTPUT_PATH = Path("data/rag/bac_corpus.preview.json")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a validated preview corpus from Bac Informatics PDFs."
    )
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = build_corpus(args.raw_dir)
    write_preview(result, args.output)

    print("PDF audit")
    for record in result.audit_records:
        metadata = record.metadata
        kind = metadata.document_type.value if metadata is not None else "unknown"
        year = str(metadata.year) if metadata is not None else "unknown"
        status = "skipped" if record.skipped else "parsed"
        details = (
            f"exercises={record.exercise_count}, excluded={record.excluded_exercise_count}"
            if record.exercise_count or record.excluded_exercise_count
            else f"barem_entries={record.barem_entry_count}"
        )
        print(f"- {record.source.name}: {kind}, {year}, {status}, {details}")
        for warning in record.warnings:
            print(f"  warning: {warning}")

    warning_count = sum(len(record.warnings) for record in result.audit_records)
    print("\nSummary")
    print(f"PDFs scanned: {result.pdfs_scanned}")
    print(f"PDFs successfully parsed: {result.pdfs_parsed}")
    print(f"PDFs skipped: {result.pdfs_skipped}")
    print(f"Exercises extracted: {len(result.documents)}")
    print(f"Exercises excluded: {len(result.excluded_exercises)}")
    for exercise in result.excluded_exercises:
        print(
            f"- {exercise.source.name}: S{exercise.section} ex{exercise.number}: "
            f"{exercise.reason}"
        )
    print(f"Grading guides parsed separately: {len(result.parsed_bareme)}")
    print(f"Warnings / ambiguities: {warning_count}")
    print(f"Preview corpus: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

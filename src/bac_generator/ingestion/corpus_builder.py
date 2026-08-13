import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from pydantic import TypeAdapter

from bac_generator.ingestion.barem_parser import parse_barem
from bac_generator.ingestion.document_classifier import classify_document
from bac_generator.ingestion.exercise_parser import parse_subject
from bac_generator.ingestion.metadata_mapper import map_retrieval_document
from bac_generator.ingestion.models import (
    BuildResult,
    DocumentType,
    ExtractedPdf,
    PdfAuditRecord,
)
from bac_generator.ingestion.normalizer import normalize_extracted_text
from bac_generator.ingestion.pdf_extractor import extract_pdf
from bac_generator.schemas.retrieval import RetrievalDocument

Extractor = Callable[[Path], ExtractedPdf]
_DOCUMENT_ADAPTER = TypeAdapter(list[RetrievalDocument])


def _pdf_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.is_dir():
        raise FileNotFoundError(f"raw PDF directory not found: {raw_dir}")
    return sorted(
        (
            path
            for path in raw_dir.rglob("*")
            if path.is_file() and path.suffix.lower() == ".pdf"
        ),
        key=lambda path: str(path).lower(),
    )


def _append_pairing_warnings(result: BuildResult) -> None:
    subject_keys = {
        record.metadata.pairing_key
        for record in result.audit_records
        if not record.skipped
        and record.metadata is not None
        and record.metadata.document_type is DocumentType.SUBJECT
    }
    barem_keys = {
        record.metadata.pairing_key
        for record in result.audit_records
        if not record.skipped
        and record.metadata is not None
        and record.metadata.document_type is DocumentType.BAREM
    }
    updated: list[PdfAuditRecord] = []
    for record in result.audit_records:
        metadata = record.metadata
        if record.skipped or metadata is None:
            updated.append(record)
            continue
        counterpart = barem_keys if metadata.document_type is DocumentType.SUBJECT else subject_keys
        if metadata.pairing_key not in counterpart:
            warning = (
                "no matching grading guide found"
                if metadata.document_type is DocumentType.SUBJECT
                else "no matching subject found"
            )
            record = replace(record, warnings=(*record.warnings, warning))
        updated.append(record)
    result.audit_records = updated


def build_corpus(raw_dir: Path, *, extractor: Extractor = extract_pdf) -> BuildResult:
    result = BuildResult()
    document_ids: set[str] = set()

    for path in _pdf_files(raw_dir):
        extraction_works = False
        metadata = None
        warnings: tuple[str, ...] = ()
        try:
            extracted = extractor(path)
            extraction_works = True
            warnings = extracted.warnings
            metadata = classify_document(extracted.text, path)
            normalized_text, normalization_warnings = normalize_extracted_text(extracted.text)
            warnings = (*extracted.warnings, *metadata.warnings, *normalization_warnings)
            if normalization_warnings:
                raise ValueError("PDF skipped because unresolved embedded-font glyphs remain")

            if metadata.document_type is DocumentType.SUBJECT:
                parsed = parse_subject(normalized_text, metadata, path)
                result.excluded_exercises.extend(parsed.excluded_exercises)
                documents = [
                    map_retrieval_document(metadata, exercise, path)
                    for exercise in parsed.exercises
                ]
                new_ids = {document.id for document in documents}
                duplicates = sorted(new_ids & document_ids)
                if duplicates:
                    raise ValueError(f"duplicate retrieval IDs: {', '.join(duplicates)}")
                document_ids.update(new_ids)
                result.documents.extend(documents)
                result.audit_records.append(
                    PdfAuditRecord(
                        source=path,
                        extraction_works=True,
                        parsing_reliable=True,
                        skipped=False,
                        metadata=metadata,
                        exercise_count=len(parsed.exercises),
                        excluded_exercise_count=len(parsed.excluded_exercises),
                        warnings=warnings,
                    )
                )
            else:
                parsed = parse_barem(normalized_text, metadata, path)
                result.parsed_bareme.append(parsed)
                result.audit_records.append(
                    PdfAuditRecord(
                        source=path,
                        extraction_works=True,
                        parsing_reliable=True,
                        skipped=False,
                        metadata=metadata,
                        barem_entry_count=len(parsed.barem_entries),
                        warnings=warnings,
                    )
                )
        except Exception as exc:
            error = str(exc)
            preserved_warnings = tuple(dict.fromkeys((*warnings, error)))
            result.audit_records.append(
                PdfAuditRecord(
                    source=path,
                    extraction_works=extraction_works,
                    parsing_reliable=False,
                    skipped=True,
                    metadata=metadata,
                    warnings=preserved_warnings,
                )
            )

    _DOCUMENT_ADAPTER.validate_python([document.model_dump() for document in result.documents])
    _append_pairing_warnings(result)
    return result


def write_preview(result: BuildResult, output_path: Path) -> None:
    if not output_path.name.endswith(".preview.json"):
        raise ValueError("output filename must end with .preview.json")
    payload = [document.model_dump(mode="json") for document in result.documents]
    _DOCUMENT_ADAPTER.validate_python(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(output_path)

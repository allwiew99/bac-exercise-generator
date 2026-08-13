from pathlib import Path

import pytest

from bac_generator.ingestion.corpus_builder import build_corpus, write_preview
from bac_generator.ingestion.models import ExtractedPdf
from bac_generator.ingestion.pdf_extractor import PdfExtractionError


def _modern_subject() -> str:
    return """
    Examenul de bacalaureat național 2019
    Proba E. d) Informatică
    Limbajul C/C++
    Varianta 1
    Filieră teoretică, profil real, specializare științe ale naturii
    Toate subiectele sunt obligatorii.
    SUBIECTUL I
    1. Un graf orientat.
    2. Item doi.
    3. Item trei.
    4. Item patru.
    5. Item cinci.
    SUBIECTUL al II-lea
    1. Item unu.
    2. Item doi.
    3. Item trei.
    SUBIECTUL al III-lea
    1. Item unu.
    2. Item doi.
    3. Item trei.
    """


def _modern_barem() -> str:
    return """
    Examenul de bacalaureat național 2019
    Proba E. d) Informatică
    BAREM DE EVALUARE ȘI DE NOTARE
    (comun pentru limbajele C/C++ şi Pascal)
    Varianta 1
    Filieră teoretică, profil real, specializare științe ale naturii
    SUBIECTUL I
    1a 2b 3c 4d 5a
    SUBIECTUL al II-lea
    1. Rubrică unu.
    2. Rubrică doi.
    3. Rubrică trei.
    SUBIECTUL al III-lea
    1. Rubrică unu.
    2. Rubrică doi.
    3. Rubrică trei.
    """


def test_builds_subject_documents_and_keeps_barem_separate(tmp_path: Path) -> None:
    subject = tmp_path / "subject.pdf"
    barem = tmp_path / "barem.pdf"
    subject.touch()
    barem.touch()

    def extractor(path: Path) -> ExtractedPdf:
        text = _modern_subject() if path.name == "subject.pdf" else _modern_barem()
        return ExtractedPdf(source=path, pages=(text,))

    result = build_corpus(tmp_path, extractor=extractor)

    assert result.pdfs_scanned == 2
    assert result.pdfs_parsed == 2
    assert result.pdfs_skipped == 0
    assert len(result.documents) == 11
    assert len(result.parsed_bareme) == 1
    assert all("Rubrică" not in document.text for document in result.documents)
    assert any(
        "exam session is not stated" in warning
        for record in result.audit_records
        for warning in record.warnings
    )


def test_skips_malformed_pdf_and_continues(tmp_path: Path) -> None:
    good = tmp_path / "good.pdf"
    bad = tmp_path / "bad.pdf"
    good.touch()
    bad.touch()

    def extractor(path: Path) -> ExtractedPdf:
        if path.name == "bad.pdf":
            raise PdfExtractionError("bad.pdf: malformed")
        return ExtractedPdf(source=path, pages=(_modern_subject(),))

    result = build_corpus(tmp_path, extractor=extractor)

    assert len(result.documents) == 11
    assert result.pdfs_skipped == 1
    skipped = next(record for record in result.audit_records if record.skipped)
    assert skipped.source.name == "bad.pdf"
    assert skipped.extraction_works is False
    assert skipped.warnings == ("bad.pdf: malformed",)


def test_duplicate_document_ids_skip_the_duplicate_pdf(tmp_path: Path) -> None:
    first = tmp_path / "a.pdf"
    second = tmp_path / "b.pdf"
    first.touch()
    second.touch()

    def extractor(path: Path) -> ExtractedPdf:
        return ExtractedPdf(source=path, pages=(_modern_subject(),))

    result = build_corpus(tmp_path, extractor=extractor)

    assert len(result.documents) == 11
    assert result.pdfs_skipped == 1
    assert any(
        "duplicate retrieval IDs" in warning
        for record in result.audit_records
        for warning in record.warnings
    )
    skipped = next(record for record in result.audit_records if record.skipped)
    assert "exam session is not stated in the PDF" in skipped.warnings


def test_writes_only_preview_filename_and_preserves_existing_corpus(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    source = raw_dir / "subject.pdf"
    source.touch()
    existing = tmp_path / "bac_corpus.json"
    existing.write_text("do-not-touch", encoding="utf-8")
    preview = tmp_path / "bac_corpus.preview.json"

    result = build_corpus(
        raw_dir,
        extractor=lambda path: ExtractedPdf(source=path, pages=(_modern_subject(),)),
    )
    write_preview(result, preview)

    assert existing.read_text(encoding="utf-8") == "do-not-touch"
    assert preview.read_text(encoding="utf-8").startswith("[\n  {")
    with pytest.raises(ValueError, match="preview.json"):
        write_preview(result, existing)


def test_keeps_safe_siblings_and_reports_visual_exclusion(tmp_path: Path) -> None:
    subject = tmp_path / "subject.pdf"
    subject.touch()
    text = _modern_subject().replace(
        "1. Un graf orientat.",
        "1. Un graf orientat cu 5 noduri este reprezentat alăturat.",
    )

    result = build_corpus(
        tmp_path,
        extractor=lambda path: ExtractedPdf(source=path, pages=(text,)),
    )

    assert len(result.documents) == 10
    assert len(result.excluded_exercises) == 1
    excluded = result.excluded_exercises[0]
    assert excluded.source == subject
    assert excluded.section == "I"
    assert excluded.number == 1
    assert excluded.reason == "missing_required_visual"
    assert result.audit_records[0].exercise_count == 10
    assert result.audit_records[0].excluded_exercise_count == 1

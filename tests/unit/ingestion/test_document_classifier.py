from pathlib import Path

import pytest

from bac_generator.ingestion.document_classifier import (
    DocumentClassificationError,
    classify_document,
)
from bac_generator.ingestion.models import DocumentType


def test_classifies_subject_from_content_not_misleading_filename() -> None:
    text = """
    Examenul de bacalaureat național 2019
    Proba E. d) Informatică
    Limbajul C/C++
    Varianta 4
    Filieră teoretică, profil real, specializare științe ale naturii
    Toate subiectele sunt obligatorii.
    SUBIECTUL I
    """

    metadata = classify_document(text, Path("pretins_barem_2020.pdf"))

    assert metadata.document_type is DocumentType.SUBJECT
    assert metadata.year == 2019
    assert metadata.session is None
    assert metadata.variant == "4"
    assert metadata.profile == "SN"
    assert metadata.programming_language == "C/C++"


@pytest.mark.parametrize(
    ("marker", "expected_session"),
    (("Simulare", "simulation"), ("MODEL", "model")),
)
def test_preserves_only_explicit_session_markers(
    marker: str, expected_session: str
) -> None:
    text = f"""
    Examenul de bacalaureat național 2020
    Informatică
    Limbajul C/C++
    {marker}
    Filieră teoretică, matematică-informatică
    Toate subiectele sunt obligatorii.
    """

    metadata = classify_document(text, Path("arbitrary.pdf"))

    assert metadata.session == expected_session
    assert metadata.variant is None


def test_classifies_common_barem_and_pascal_profile() -> None:
    text = """
    Examenul de bacalaureat național 2017
    Informatică
    BAREM DE EVALUARE ȘI DE NOTARE
    (comun pentru limbajele C/C++ şi Pascal)
    Varianta 3
    Filieră teoretică, profil real, specializarea științe ale naturii
    SUBIECTUL I
    """

    metadata = classify_document(text, Path("subject.pdf"))

    assert metadata.document_type is DocumentType.BAREM
    assert metadata.programming_language == "C/C++ + Pascal"
    assert metadata.profile == "SN"


def test_rejects_incomplete_metadata() -> None:
    with pytest.raises(DocumentClassificationError, match="year"):
        classify_document("Informatică\nSUBIECTUL I", Path("unknown.pdf"))

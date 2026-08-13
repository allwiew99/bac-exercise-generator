from pathlib import Path

from bac_generator.ingestion.barem_parser import parse_barem
from bac_generator.ingestion.models import BacMetadata, DocumentType


def test_parses_barem_entries_without_creating_subject_exercises() -> None:
    text = """
    SUBIECTUL I (20 de puncte)
    1a 2b 3c 4d 5a 5x4p.
    SUBIECTUL al II-lea (40 de puncte)
    1. a) Răspuns corect: 10
    b) Alt răspuns.
    2. Pentru rezolvare corectă.
    3. Pentru rezolvare corectă.
    SUBIECTUL al III-lea (30 de puncte)
    1. Pentru subprogram corect.
    2. Pentru program corect.
    3. Pentru algoritm corect.
    """
    metadata = BacMetadata(
        year=2019,
        document_type=DocumentType.BAREM,
        profile="SN",
        programming_language="C/C++ + Pascal",
        variant="1",
    )

    parsed = parse_barem(text, metadata, Path("barem.pdf"))

    assert parsed.exercises == ()
    assert len(parsed.barem_entries) == 11
    assert parsed.barem_entries[0].text == "Răspuns: a"
    assert parsed.barem_entries[5].section == "II"
    assert "b) Alt răspuns." in parsed.barem_entries[5].text

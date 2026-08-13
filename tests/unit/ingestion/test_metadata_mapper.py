from pathlib import Path

from bac_generator.ingestion.metadata_mapper import (
    build_document_id,
    map_retrieval_document,
)
from bac_generator.ingestion.models import BacMetadata, DocumentType, ParsedExercise


def test_builds_collision_resistant_id_for_unstated_exam_session() -> None:
    metadata = BacMetadata(
        year=2019,
        document_type=DocumentType.SUBJECT,
        profile="MI",
        programming_language="C/C++",
        variant="1",
    )

    document_id = build_document_id(metadata, "II", 2)

    assert document_id == "bac-2019-exam-v01-mi-cpp-s2-ex2"


def test_builds_ids_for_explicit_model_and_pascal_simulation() -> None:
    model = BacMetadata(
        year=2020,
        document_type=DocumentType.SUBJECT,
        profile="SN",
        programming_language="C/C++",
        session="model",
    )
    simulation = BacMetadata(
        year=2019,
        document_type=DocumentType.SUBJECT,
        profile="SN",
        programming_language="Pascal",
        session="simulation",
    )

    assert build_document_id(model, "I", 1) == "bac-2020-model-sn-cpp-s1-ex1"
    assert (
        build_document_id(simulation, "III", 4)
        == "bac-2019-simulation-sn-pascal-s3-ex4"
    )


def test_maps_exercise_without_inventing_difficulty_or_language_metadata() -> None:
    metadata = BacMetadata(
        year=2018,
        document_type=DocumentType.SUBJECT,
        profile="SN",
        programming_language="C/C++",
        variant="8",
    )
    exercise = ParsedExercise(
        section="II",
        number=1,
        text="1. Un graf orientat are cinci vârfuri.",
    )

    document = map_retrieval_document(
        metadata,
        exercise,
        Path("data/rag/raw/source.pdf"),
    )

    assert document.id == "bac-2018-exam-v08-sn-cpp-s2-ex1"
    assert document.source == "data/rag/raw/source.pdf"
    assert document.topic == "graphs"
    assert document.year == 2018
    assert document.bac_section == "subiectul_II"
    assert document.exercise_type == "open_response"
    assert document.difficulty is None
    assert document.language == "ro"
    assert document.text.startswith(
        "Context: Bacalaureat 2018; sesiune nespecificată; varianta 8; "
        "profil SN; limbaj C/C++; Subiectul II; exercițiul 1."
    )

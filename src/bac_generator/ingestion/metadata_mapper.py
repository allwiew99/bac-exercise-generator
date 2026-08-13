import re
from pathlib import Path

from bac_generator.ingestion.models import BacMetadata, DocumentType, ParsedExercise
from bac_generator.ingestion.topic_classifier import classify_exercise_type, classify_topic
from bac_generator.schemas.retrieval import RetrievalDocument

_SECTION_NUMBERS = {"I": 1, "II": 2, "III": 3}
_LANGUAGE_SLUGS = {"C/C++": "cpp", "Pascal": "pascal"}


def _variant_slug(variant: str) -> str:
    if variant.isdigit():
        return f"v{int(variant):02d}"
    return f"v-{re.sub(r'[^a-z0-9]+', '-', variant.lower()).strip('-')}"


def build_document_id(metadata: BacMetadata, section: str, exercise_number: int) -> str:
    if metadata.document_type is not DocumentType.SUBJECT:
        raise ValueError("retrieval IDs can only be built for subject exercises")
    if section not in _SECTION_NUMBERS:
        raise ValueError(f"unsupported Bac section: {section}")
    language = _LANGUAGE_SLUGS.get(metadata.programming_language)
    if language is None:
        raise ValueError("common-language barem metadata cannot identify a subject exercise")

    identity: str = metadata.session or "exam"
    if metadata.variant is not None:
        identity = f"{identity}-{_variant_slug(metadata.variant)}"
    return (
        f"bac-{metadata.year}-{identity}-{metadata.profile.lower()}-{language}-"
        f"s{_SECTION_NUMBERS[section]}-ex{exercise_number}"
    )


def _context(metadata: BacMetadata, exercise: ParsedExercise) -> str:
    if metadata.session == "simulation":
        session = "simulare"
    elif metadata.session == "model":
        session = "model"
    else:
        session = "sesiune nespecificată"
    variant = f"; varianta {metadata.variant}" if metadata.variant is not None else ""
    return (
        f"Context: Bacalaureat {metadata.year}; {session}{variant}; "
        f"profil {metadata.profile}; limbaj {metadata.programming_language}; "
        f"Subiectul {exercise.section}; exercițiul {exercise.number}."
    )


def map_retrieval_document(
    metadata: BacMetadata,
    exercise: ParsedExercise,
    source: Path,
) -> RetrievalDocument:
    topic = classify_topic(exercise.text)
    exercise_type = classify_exercise_type(exercise.text)
    return RetrievalDocument(
        id=build_document_id(metadata, exercise.section, exercise.number),
        text=f"{_context(metadata, exercise)}\n\n{exercise.text}",
        source=str(source),
        topic=topic,
        year=metadata.year,
        bac_section=f"subiectul_{exercise.section}",
        exercise_type=exercise_type,
        difficulty=None,
        language="ro",
    )

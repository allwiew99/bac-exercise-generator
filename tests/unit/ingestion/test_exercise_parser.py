from pathlib import Path

import pytest

from bac_generator.ingestion.exercise_parser import ExerciseParsingError, parse_subject
from bac_generator.ingestion.models import BacMetadata, DocumentType


def _metadata(year: int, profile: str = "MI") -> BacMetadata:
    return BacMetadata(
        year=year,
        document_type=DocumentType.SUBJECT,
        profile=profile,  # type: ignore[arg-type]
        programming_language="C/C++",
        variant="1",
    )


def _modern_subject_with_items(items: dict[tuple[str, int], str]) -> str:
    sections: list[str] = []
    for section, count in (("I", 5), ("II", 3), ("III", 3)):
        sections.append(f"SUBIECTUL {section}")
        sections.extend(
            f"{number}. {items.get((section, number), f'Exercițiul {section}.{number}')}"
            for number in range(1, count + 1)
        )
    return "\n".join(sections)


def test_splits_2019_layout_into_semantic_exercises_and_keeps_subpoints() -> None:
    text = """
    SUBIECTUL I (20 de puncte)
    1. Exercițiul I.1
    a. A b. B c. C d. D
    2. Exercițiul I.2
    3. Exercițiul I.3
    4. Exercițiul I.4
    5. Exercițiul I.5
    SUBIECTUL al II-lea (40 de puncte)
    1. Algoritmul alăturat este reprezentat în pseudocod.
    a) Cerința a.
    b) Cerința b.
    2. Exercițiul II.2
    3. Exercițiul II.3
    SUBIECTUL al III - lea (30 de puncte)
    1. Exercițiul III.1
    2. Exercițiul III.2
    3. Exercițiul III.3
    """

    parsed = parse_subject(text, _metadata(2019), Path("subject.pdf"))

    assert len(parsed.exercises) == 11
    assert [(item.section, item.number) for item in parsed.exercises] == [
        ("I", 1),
        ("I", 2),
        ("I", 3),
        ("I", 4),
        ("I", 5),
        ("II", 1),
        ("II", 2),
        ("II", 3),
        ("III", 1),
        ("III", 2),
        ("III", 3),
    ]
    assert "a) Cerința a." in parsed.exercises[5].text
    assert "b) Cerința b." in parsed.exercises[5].text


def test_splits_2017_layout_with_legacy_section_counts() -> None:
    sections = (
        "SUBIECTUL I\n" + "\n".join(f"{number}. I-{number}" for number in range(1, 3)),
        "SUBIECTUL al II-lea\n"
        + "\n".join(f"{number}. II-{number}" for number in range(1, 6)),
        "SUBIECTUL al III-lea\n"
        + "\n".join(f"{number}. III-{number}" for number in range(1, 5)),
    )

    parsed = parse_subject("\n".join(sections), _metadata(2017), Path("legacy.pdf"))

    assert len(parsed.exercises) == 11
    assert parsed.exercises[-1].section == "III"
    assert parsed.exercises[-1].number == 4


def test_splits_legacy_sciences_profile_with_four_section_ii_exercises() -> None:
    sections = (
        "SUBIECTUL I\n" + "\n".join(f"{number}. I-{number}" for number in range(1, 3)),
        "SUBIECTUL al II-lea\n"
        + "\n".join(f"{number}. II-{number}" for number in range(1, 5)),
        "SUBIECTUL al III – lea\n"
        + "\n".join(f"{number}. III-{number}" for number in range(1, 5)),
    )

    parsed = parse_subject(
        "\n".join(sections),
        _metadata(2017, profile="SN"),
        Path("sciences.pdf"),
    )

    assert len(parsed.exercises) == 10


def test_rejects_subject_with_unexpected_exercise_count() -> None:
    text = """
    SUBIECTUL I
    1. Un singur exercițiu
    SUBIECTUL al II-lea
    1. Un singur exercițiu
    SUBIECTUL al III-lea
    1. Un singur exercițiu
    """

    with pytest.raises(ExerciseParsingError, match="expected 5 exercises in section I"):
        parse_subject(text, _metadata(2020), Path("incomplete.pdf"))


def test_removes_shared_section_direction_without_removing_item_instruction() -> None:
    text = "\n".join(
        (
            "SUBIECTUL I",
            "1. I-1",
            "2. I-2",
            "SUBIECTUL al II-lea",
            "1. II-1",
            "2. II-2",
            "Scrieţi pe foaia de examen răspunsul pentru fiecare dintre cerinţele următoare.",
            "3. Scrieţi pe foaia de examen răspunsul cerut pentru acest exercițiu.",
            "4. II-4",
            "5. II-5",
            "SUBIECTUL al III-lea",
            "1. III-1",
            "2. III-2",
            "3. III-3",
            "4. III-4",
        )
    )

    parsed = parse_subject(text, _metadata(2017), Path("legacy.pdf"))

    section_two = [exercise for exercise in parsed.exercises if exercise.section == "II"]
    assert "fiecare dintre cerinţele următoare" not in section_two[1].text
    assert "răspunsul cerut pentru acest exercițiu" in section_two[2].text


def test_excludes_graph_requiring_missing_visual_but_keeps_textual_matrix() -> None:
    text = _modern_subject_with_items(
        {
            ("I", 1): (
                "Un graf cu 5 noduri este reprezentat\n"
                "alăturat. Indicați răspunsul."
            ),
            ("I", 2): (
                "Un graf este reprezentat prin matricea de adiacență alăturată.\n"
                "0 1 0 1\n1 0 1 0\n0 1 0 1\n1 0 1 0"
            ),
        }
    )

    parsed = parse_subject(text, _metadata(2020), Path("visual.pdf"))

    assert [(item.section, item.number, item.reason) for item in parsed.excluded_exercises] == [
        ("I", 1, "missing_required_visual")
    ]
    assert any(item.section == "I" and item.number == 2 for item in parsed.exercises)


def test_excludes_exercise_with_ambiguous_math_notation_marker() -> None:
    text = _modern_subject_with_items(
        {("III", 1): "Calculați expresia ⟦unsafe:ambiguous_math_notation⟧."}
    )

    parsed = parse_subject(text, _metadata(2020), Path("notation.pdf"))

    assert parsed.excluded_exercises[0].reason == "ambiguous_math_notation"
    assert all(item.number != 1 for item in parsed.exercises if item.section == "III")


def test_excludes_exercise_with_unreliable_pseudocode_layout_marker() -> None:
    text = _modern_subject_with_items(
        {
            ("II", 1): (
                "Algoritmul este în pseudocod. "
                "⟦unsafe:unreliable_pseudocode_layout⟧"
            )
        }
    )

    parsed = parse_subject(text, _metadata(2020), Path("pseudocode.pdf"))

    assert parsed.excluded_exercises[0].reason == "unreliable_pseudocode_layout"


@pytest.mark.parametrize(
    "corrupted_text",
    (
        "liter , corespunz toare tipului.\nă ă Ș ă",
        "Exemplu:\natu n ci p e e c ra n se afi ș ea ză v a lor il e:",
    ),
)
def test_excludes_exercise_with_unreliable_text_layout(corrupted_text: str) -> None:
    text = _modern_subject_with_items({("III", 1): corrupted_text})

    parsed = parse_subject(text, _metadata(2020), Path("layout.pdf"))

    assert parsed.excluded_exercises[0].reason == "unreliable_text_layout"


def test_fragmented_text_check_does_not_reject_textual_matrix_rows() -> None:
    text = _modern_subject_with_items(
        {
            ("II", 3): (
                "Variabila m memorează un tablou a b c d e f g.\n"
                "+ a b c d e f\n+ + a b c d e"
            )
        }
    )

    parsed = parse_subject(text, _metadata(2020), Path("matrix.pdf"))

    assert any(item.section == "II" and item.number == 3 for item in parsed.exercises)

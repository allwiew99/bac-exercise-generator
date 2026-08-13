import pytest

from bac_generator.ingestion.topic_classifier import (
    classify_exercise_type,
    classify_topic,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("Un graf orientat are 10 arce și 5 vârfuri.", "graphs"),
        ("Un arbore este reprezentat prin vectorul de tați.", "trees"),
        ("Utilizând metoda backtracking se generează soluțiile.", "combinatorics/backtracking"),
        ("Algoritmul alăturat este reprezentat în pseudocod.", "pseudocode"),
        ("Se prelucrează o matrice cu n linii și n coloane.", "matrices"),
        ("Fișierul bac.in conține numere naturale.", "files"),
    ),
)
def test_assigns_topic_only_for_strong_deterministic_signal(text: str, expected: str) -> None:
    assert classify_topic(text) == expected


def test_conflicting_topic_signals_are_unclassified() -> None:
    text = "Se citește un graf memorat într-un tablou unidimensional."

    assert classify_topic(text) == "unclassified"


def test_absent_topic_signal_is_unclassified() -> None:
    assert classify_topic("Indicați expresia corectă.") == "unclassified"


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("1. Indicați expresia.\na. 1 b. 2 c. 3 d. 4", "multiple_choice"),
        (
            "Algoritmul este în pseudocod.\na) Scrieți valoarea.\nb) Rescrieți.",
            "pseudocode_analysis",
        ),
        ("Scrieți definiția completă a subprogramului f.", "subprogram_implementation"),
        ("Scrieți programul C/C++ corespunzător.", "program_implementation"),
        ("Determinați valorile cerute.", "open_response"),
    ),
)
def test_classifies_exercise_type_deterministically(text: str, expected: str) -> None:
    assert classify_exercise_type(text) == expected

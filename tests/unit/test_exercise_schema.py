import pytest
from pydantic import ValidationError

from bac_generator.schemas.exercise import Difficulty, ExerciseRequest, ExerciseResponse


def test_exercise_request_accepts_valid_data() -> None:
    exercise_request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.EASY,
    )

    assert exercise_request.topic == "vectori"
    assert exercise_request.difficulty is Difficulty.EASY


def test_exercise_request_rejects_invalid_difficulty() -> None:
    with pytest.raises(ValidationError):
        ExerciseRequest.model_validate(
            {
                "topic": "vectori",
                "difficulty": "invalid",
            }
        )


def test_exercise_response_accepts_valid_data() -> None:
    exercise_response = ExerciseResponse(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
        statement="Se citește un vector cu n elemente. Determină suma elementelor pare.",
        solution="Parcurgem vectorul și adunăm elementele care sunt divizibile cu 2.",
        explanation="Folosim o singură parcurgere, deci complexitatea este O(n).",
    )

    assert exercise_response.topic == "vectori"
    assert exercise_response.difficulty is Difficulty.MEDIUM
    assert (
        exercise_response.statement
        == "Se citește un vector cu n elemente. Determină suma elementelor pare."
    )
    assert (
        exercise_response.solution
        == "Parcurgem vectorul și adunăm elementele care sunt divizibile cu 2."
    )
    assert (
        exercise_response.explanation
        == "Folosim o singură parcurgere, deci complexitatea este O(n)."
    )

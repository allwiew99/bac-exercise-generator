import pytest

from bac_generator.core.exceptions import ExerciseValidationError
from bac_generator.schemas.exercise import (
    Difficulty,
    ExerciseRequest,
    ExerciseResponse,
)
from bac_generator.services.exercise_validator import ExerciseValidator


class FakeCodeValidator:
    def validate_cpp(self, code: str) -> None:
        pass


def test_validate_accepts_valid_exercise() -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    exercise = ExerciseResponse(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
        statement="Enunț valid.",
        solution="Soluție validă.",
        explanation="Explicație validă.",
    )

    validator.validate(request, exercise)


def test_validate_rejects_mismatched_topic() -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    exercise = ExerciseResponse(
        topic="matrici",
        difficulty=Difficulty.MEDIUM,
        statement="Enunț valid.",
        solution="Soluție validă.",
        explanation="Explicație validă.",
    )

    with pytest.raises(
        ExerciseValidationError,
        match="does not match requested topic",
    ):
        validator.validate(request, exercise)


def test_validate_rejects_mismatched_difficulty() -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    exercise = ExerciseResponse(
        topic="vectori",
        difficulty=Difficulty.HARD,
        statement="Enunț valid.",
        solution="Soluție validă.",
        explanation="Explicație validă.",
    )

    with pytest.raises(
        ExerciseValidationError,
        match="does not match requested difficulty",
    ):
        validator.validate(request, exercise)


def test_validate_rejects_empty_statement() -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    exercise = ExerciseResponse(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
        statement="",
        solution="Soluție validă.",
        explanation="Explicație validă.",
    )

    with pytest.raises(
        ExerciseValidationError,
        match="The generated 'statement' field is empty",
    ):
        validator.validate(request, exercise)

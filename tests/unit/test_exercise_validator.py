import pytest

from bac_generator.core.exceptions import ExerciseValidationError
from bac_generator.schemas.exercise import (
    Difficulty,
    ExerciseRequest,
    ExerciseResponse,
    ExerciseTestCase,
)
from bac_generator.services.exercise_validator import ExerciseValidator


class FakeCodeValidator:
    def validate_cpp(self, code: str) -> None:
        pass

    def validate_cpp_with_test_cases(
        self,
        code: str,
        test_cases: list[ExerciseTestCase],
    ) -> None:
        pass


def build_valid_test_cases() -> list[ExerciseTestCase]:
    return [
        ExerciseTestCase(
            input="3\n1 2 4",
            expected_output="6",
            is_hidden=False,
        ),
        ExerciseTestCase(
            input="2\n5 5",
            expected_output="10",
            is_hidden=True,
        ),
        ExerciseTestCase(
            input="1\n7",
            expected_output="7",
            is_hidden=True,
        ),
        ExerciseTestCase(
            input="4\n1 1 1 1",
            expected_output="4",
            is_hidden=True,
        ),
    ]


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
        test_cases=build_valid_test_cases(),
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
        test_cases=build_valid_test_cases(),
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
        test_cases=build_valid_test_cases(),
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
        test_cases=build_valid_test_cases(),
    )

    with pytest.raises(
        ExerciseValidationError,
        match="The generated 'statement' field is empty",
    ):
        validator.validate(request, exercise)


def test_validate_rejects_too_few_test_cases() -> None:
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
        test_cases=[
            ExerciseTestCase(
                input="1",
                expected_output="1",
                is_hidden=False,
            ),
            ExerciseTestCase(
                input="2",
                expected_output="2",
                is_hidden=True,
            ),
            ExerciseTestCase(
                input="3",
                expected_output="3",
                is_hidden=True,
            ),
        ],
    )

    with pytest.raises(
        ExerciseValidationError,
        match="between 4 and 6 test cases",
    ):
        validator.validate(request, exercise)


def test_validate_rejects_too_many_test_cases() -> None:
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
        test_cases=[
            ExerciseTestCase(
                input=str(index),
                expected_output=str(index),
                is_hidden=index != 1,
            )
            for index in range(1, 8)
        ],
    )

    with pytest.raises(
        ExerciseValidationError,
        match="between 4 and 6 test cases",
    ):
        validator.validate(request, exercise)


def test_validate_rejects_no_public_test_cases() -> None:
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
        test_cases=[
            ExerciseTestCase(
                input="1",
                expected_output="1",
                is_hidden=True,
            ),
            ExerciseTestCase(
                input="2",
                expected_output="2",
                is_hidden=True,
            ),
            ExerciseTestCase(
                input="3",
                expected_output="3",
                is_hidden=True,
            ),
            ExerciseTestCase(
                input="4",
                expected_output="4",
                is_hidden=True,
            ),
        ],
    )

    with pytest.raises(
        ExerciseValidationError,
        match="1 or 2 public sample test cases",
    ):
        validator.validate(request, exercise)


def test_validate_rejects_more_than_two_public_test_cases() -> None:
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
        test_cases=[
            ExerciseTestCase(
                input="1",
                expected_output="1",
                is_hidden=False,
            ),
            ExerciseTestCase(
                input="2",
                expected_output="2",
                is_hidden=False,
            ),
            ExerciseTestCase(
                input="3",
                expected_output="3",
                is_hidden=False,
            ),
            ExerciseTestCase(
                input="4",
                expected_output="4",
                is_hidden=True,
            ),
        ],
    )

    with pytest.raises(
        ExerciseValidationError,
        match="1 or 2 public sample test cases",
    ):
        validator.validate(request, exercise)


def test_validate_rejects_duplicate_test_cases() -> None:
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
        test_cases=[
            ExerciseTestCase(
                input="1",
                expected_output="1",
                is_hidden=False,
            ),
            ExerciseTestCase(
                input="2",
                expected_output="2",
                is_hidden=True,
            ),
            ExerciseTestCase(
                input="2",
                expected_output="2",
                is_hidden=True,
            ),
            ExerciseTestCase(
                input="4",
                expected_output="4",
                is_hidden=True,
            ),
        ],
    )

    with pytest.raises(
        ExerciseValidationError,
        match="duplicate test cases",
    ):
        validator.validate(request, exercise)
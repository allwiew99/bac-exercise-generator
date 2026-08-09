import logging

from bac_generator.core.exceptions import (
    CodeCompilationError,
    ExerciseValidationError,
)
from bac_generator.schemas.exercise import ExerciseRequest, ExerciseResponse
from bac_generator.services.code_validator_protocol import CodeValidatorProtocol

logger = logging.getLogger(__name__)


class ExerciseValidator:
    def __init__(self, code_validator: CodeValidatorProtocol) -> None:
        self.code_validator = code_validator

    def validate(
        self,
        request: ExerciseRequest,
        exercise: ExerciseResponse,
    ) -> None:
        logger.info(
            "Starting exercise validation for topic '%s' with difficulty '%s'.",
            request.topic,
            request.difficulty,
        )

        if request.topic != exercise.topic:
            raise ExerciseValidationError(
                f"Generated topic '{exercise.topic}' does not match "
                f"requested topic '{request.topic}'."
            )

        if request.difficulty != exercise.difficulty:
            raise ExerciseValidationError(
                f"Generated difficulty '{exercise.difficulty}' does not match "
                f"requested difficulty '{request.difficulty}'."
            )

        if not exercise.statement.strip():
            raise ExerciseValidationError(
                "The generated 'statement' field is empty."
            )

        if not exercise.solution.strip():
            raise ExerciseValidationError(
                "The generated 'solution' field is empty."
            )

        if not exercise.explanation.strip():
            raise ExerciseValidationError(
                "The generated 'explanation' field is empty."
            )

        total_test_cases = len(exercise.test_cases)

        if total_test_cases < 4 or total_test_cases > 6:
            raise ExerciseValidationError(
                "The generated exercise must contain between "
                "4 and 6 test cases."
            )

        public_test_cases = [
            test_case
            for test_case in exercise.test_cases
            if not test_case.is_hidden
        ]

        public_test_count = len(public_test_cases)

        if public_test_count < 1 or public_test_count > 2:
            raise ExerciseValidationError(
                "The generated exercise must contain exactly "
                "1 or 2 public sample test cases."
            )

        seen_test_cases: set[tuple[str, str]] = set()

        for test_case in exercise.test_cases:
            normalized_test_case = (
                test_case.input.strip(),
                test_case.expected_output.strip(),
            )

            if normalized_test_case in seen_test_cases:
                raise ExerciseValidationError(
                    "The generated exercise contains duplicate test cases."
                )

            seen_test_cases.add(normalized_test_case)

        try:
            self.code_validator.validate_cpp_with_test_cases(
                exercise.solution,
                exercise.test_cases,
            )
        except CodeCompilationError as exc:
            raise ExerciseValidationError(
                f"The generated C++ solution is invalid. Details:\n{exc}"
            ) from exc

        logger.info(
            "Exercise validation completed successfully for topic '%s' "
            "with difficulty '%s'.",
            exercise.topic,
            exercise.difficulty,
        )
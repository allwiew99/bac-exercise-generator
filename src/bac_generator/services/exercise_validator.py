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
            raise ExerciseValidationError("The generated 'statement' field is empty.")

        if not exercise.solution.strip():
            raise ExerciseValidationError("The generated 'solution' field is empty.")

        if not exercise.explanation.strip():
            raise ExerciseValidationError("The generated 'explanation' field is empty.")

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
            "Exercise validation completed successfully for topic '%s' with difficulty '%s'.",
            exercise.topic,
            exercise.difficulty,
        )

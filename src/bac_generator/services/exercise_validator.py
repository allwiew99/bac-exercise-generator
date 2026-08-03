from bac_generator.schemas.exercise import ExerciseRequest, ExerciseResponse
from bac_generator.services.code_validator_protocol import CodeValidatorProtocol


class ExerciseValidator:
    def __init__(self, code_validator: CodeValidatorProtocol) -> None:
        self.code_validator = code_validator

    def validate(
        self,
        request: ExerciseRequest,
        exercise: ExerciseResponse,
    ) -> None:
        if request.topic != exercise.topic:
            raise ValueError(
                f"Exercise topic '{exercise.topic}' does not match "
                f"requested topic '{request.topic}'."
            )

        if request.difficulty != exercise.difficulty:
            raise ValueError(
                f"Exercise difficulty '{exercise.difficulty}' does not match "
                f"requested difficulty '{request.difficulty}'."
            )

        if (
            not exercise.statement.strip()
            or not exercise.solution.strip()
            or not exercise.explanation.strip()
        ):
            raise ValueError(
                "Exercise statement, solution, and explanation must not be empty."
            )

        self.code_validator.validate_cpp(exercise.solution)
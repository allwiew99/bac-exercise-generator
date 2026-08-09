from bac_generator.schemas.exercise import ExerciseTestCase
from bac_generator.services.code_runner_protocol import (
    CodeRunnerProtocol,
)
from bac_generator.services.local_code_runner import (
    LocalCodeRunner,
)


class CodeValidator:
    def __init__(
        self,
        runner: CodeRunnerProtocol | None = None,
    ) -> None:
        self.runner = runner or LocalCodeRunner()

    def validate_cpp(
        self,
        code: str,
    ) -> None:
        self.runner.validate_cpp(code)

    def validate_cpp_with_test_cases(
        self,
        code: str,
        test_cases: list[ExerciseTestCase],
    ) -> None:
        self.runner.validate_cpp_with_test_cases(
            code,
            test_cases,
        )
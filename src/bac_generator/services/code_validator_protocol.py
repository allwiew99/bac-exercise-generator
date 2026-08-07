from typing import Protocol

from bac_generator.schemas.exercise import ExerciseTestCase


class CodeValidatorProtocol(Protocol):
    def validate_cpp(self, code: str) -> None:
        ...

    def validate_cpp_with_test_cases(
        self,
        code: str,
        test_cases: list[ExerciseTestCase],
    ) -> None:
        ...
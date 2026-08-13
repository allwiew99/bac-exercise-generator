from pathlib import Path

from bac_generator.core.exceptions import CodeCompilationError
from bac_generator.evaluation.sandbox_validation import run_sandbox_validation
from bac_generator.schemas.exercise import ExerciseTestCase


class ContractAwareRunner:
    def validate_cpp(self, code: str) -> None:
        raise AssertionError("validation must exercise stdin/stdout test cases")

    def validate_cpp_with_test_cases(
        self,
        code: str,
        test_cases: list[ExerciseTestCase],
    ) -> None:
        if "return 7" in code:
            raise CodeCompilationError("Program execution failed")
        if "while (true)" in code:
            raise CodeCompilationError(
                "Program execution timed out after 2 seconds."
            )
        assert test_cases == [
            ExerciseTestCase(input="21\n", expected_output="42\n")
        ]


def test_sandbox_validation_covers_all_required_runtime_contracts(
    tmp_path: Path,
) -> None:
    sandbox_binary = tmp_path / "sandbox"
    sandbox_binary.touch()

    report = run_sandbox_validation(
        runner=ContractAwareRunner(),
        sandbox_binary=sandbox_binary,
    )

    assert report.success is True
    assert report.binary_present is True
    assert report.compile_run.passed is True
    assert report.stdin_stdout.passed is True
    assert report.mounted_workspace.passed is True
    assert report.nonzero_exit.passed is True
    assert report.timeout.passed is True


def test_sandbox_validation_fails_cleanly_when_launcher_is_absent(
    tmp_path: Path,
) -> None:
    report = run_sandbox_validation(
        runner=ContractAwareRunner(),
        sandbox_binary=tmp_path / "missing-sandbox",
    )

    assert report.success is False
    assert report.binary_present is False
    assert report.compile_run.passed is False

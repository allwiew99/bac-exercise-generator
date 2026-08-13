import json
from pathlib import Path

from pydantic import BaseModel

from bac_generator.core.exceptions import CodeCompilationError
from bac_generator.schemas.exercise import ExerciseTestCase
from bac_generator.services.code_runner_protocol import CodeRunnerProtocol
from bac_generator.services.sandbox_code_runner import (
    SANDBOX_BINARY,
    SandboxCodeRunner,
)


class SandboxCheck(BaseModel):
    passed: bool
    detail: str


class SandboxValidationReport(BaseModel):
    sandbox_binary: str
    binary_present: bool
    compile_run: SandboxCheck
    stdin_stdout: SandboxCheck
    mounted_workspace: SandboxCheck
    nonzero_exit: SandboxCheck
    timeout: SandboxCheck
    success: bool


_SUCCESS_PROGRAM = r"""
#include <iostream>

int main() {
    long long value;
    if (!(std::cin >> value)) {
        return 2;
    }
    std::cout << value * 2 << '\n';
    return 0;
}
"""

_NONZERO_PROGRAM = r"""
int main() {
    return 7;
}
"""

_TIMEOUT_PROGRAM = r"""
int main() {
    while (true) {
    }
}
"""


def run_sandbox_validation(
    *,
    runner: CodeRunnerProtocol | None = None,
    sandbox_binary: Path = Path(SANDBOX_BINARY),
) -> SandboxValidationReport:
    binary_present = sandbox_binary.exists()
    if not binary_present:
        missing = SandboxCheck(
            passed=False,
            detail=f"Sandbox launcher does not exist: {sandbox_binary}",
        )
        return SandboxValidationReport(
            sandbox_binary=str(sandbox_binary),
            binary_present=False,
            compile_run=missing,
            stdin_stdout=missing,
            mounted_workspace=missing,
            nonzero_exit=missing,
            timeout=missing,
            success=False,
        )

    active_runner = runner or SandboxCodeRunner()
    successful_run = _expect_success(active_runner)
    nonzero_exit = _expect_rejection(
        active_runner,
        _NONZERO_PROGRAM,
        expected_fragment="Program execution failed",
        success_detail="Nonzero program exit was rejected by the sandbox runner.",
    )
    timeout = _expect_rejection(
        active_runner,
        _TIMEOUT_PROGRAM,
        expected_fragment="timed out",
        success_detail="Program exceeding the per-test timeout was rejected.",
    )
    checks = [successful_run, nonzero_exit, timeout]

    return SandboxValidationReport(
        sandbox_binary=str(sandbox_binary),
        binary_present=True,
        compile_run=successful_run,
        stdin_stdout=successful_run.model_copy(
            update={
                "detail": (
                    "Program consumed '21' from stdin and produced '42' on stdout."
                    if successful_run.passed
                    else successful_run.detail
                )
            }
        ),
        mounted_workspace=successful_run.model_copy(
            update={
                "detail": (
                    "Compilation and test execution succeeded from the bind-mounted "
                    "/workspace directory."
                    if successful_run.passed
                    else successful_run.detail
                )
            }
        ),
        nonzero_exit=nonzero_exit,
        timeout=timeout,
        success=all(check.passed for check in checks),
    )


def _expect_success(runner: CodeRunnerProtocol) -> SandboxCheck:
    try:
        runner.validate_cpp_with_test_cases(
            _SUCCESS_PROGRAM,
            [ExerciseTestCase(input="21\n", expected_output="42\n")],
        )
    except Exception as exc:
        return SandboxCheck(
            passed=False,
            detail=f"{type(exc).__name__}: {exc}",
        )
    return SandboxCheck(
        passed=True,
        detail="C++17 compilation and execution succeeded.",
    )


def _expect_rejection(
    runner: CodeRunnerProtocol,
    code: str,
    *,
    expected_fragment: str,
    success_detail: str,
) -> SandboxCheck:
    try:
        runner.validate_cpp_with_test_cases(
            code,
            [ExerciseTestCase(input="", expected_output="")],
        )
    except CodeCompilationError as exc:
        if expected_fragment.lower() in str(exc).lower():
            return SandboxCheck(passed=True, detail=success_detail)
        return SandboxCheck(
            passed=False,
            detail=(
                "Runner rejected the program for an unexpected reason: "
                f"{exc}"
            ),
        )
    except Exception as exc:
        return SandboxCheck(
            passed=False,
            detail=f"Unexpected {type(exc).__name__}: {exc}",
        )
    return SandboxCheck(
        passed=False,
        detail="Runner unexpectedly accepted the invalid program.",
    )


def main() -> int:
    report = run_sandbox_validation()
    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.success else 1


if __name__ == "__main__":
    raise SystemExit(main())

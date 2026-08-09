import json
import subprocess
import tempfile
from pathlib import Path

from bac_generator.core.exceptions import CodeCompilationError
from bac_generator.schemas.exercise import ExerciseTestCase

SANDBOX_BINARY = "/usr/local/gcp/bin/sandbox"


class SandboxCodeRunner:
    def validate_cpp(
        self,
        code: str,
    ) -> None:
        self.validate_cpp_with_test_cases(
            code=code,
            test_cases=[],
        )

    def validate_cpp_with_test_cases(
        self,
        code: str,
        test_cases: list[ExerciseTestCase],
    ) -> None:
        if not code.strip():
            raise CodeCompilationError(
                "Code cannot be empty."
            )

        sandbox_binary = Path(SANDBOX_BINARY)

        if not sandbox_binary.exists():
            raise CodeCompilationError(
                "Cloud Run sandbox runtime is not available."
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            source_path = workspace / "main.cpp"
            tests_path = workspace / "tests.json"
            runner_path = workspace / "run.sh"

            source_path.write_text(
                code,
                encoding="utf-8",
            )

            tests_path.write_text(
                json.dumps(
                    [
                        {
                            "input": test_case.input,
                            "expected_output": (
                                test_case.expected_output
                            ),
                        }
                        for test_case in test_cases
                    ]
                ),
                encoding="utf-8",
            )

            runner_path.write_text(
                self._build_runner_script(),
                encoding="utf-8",
            )

            runner_path.chmod(0o700)

            mount_value = (
                "type=bind,"
                f"source={workspace},"
                "destination=/workspace"
            )

            try:
                result = subprocess.run(
                    [
                        SANDBOX_BINARY,
                        "do",
                        "--write",
                        "--mount",
                        mount_value,
                        "--workdir",
                        "/workspace",
                        "--",
                        "/bin/bash",
                        "/workspace/run.sh",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=20,
                )
            except subprocess.TimeoutExpired as exc:
                raise CodeCompilationError(
                    "Sandbox execution timed out."
                ) from exc

            if result.returncode != 0:
                error_message = result.stderr.strip()

                if not error_message:
                    error_message = result.stdout.strip()

                if not error_message:
                    error_message = (
                        "Sandbox execution failed."
                    )

                raise CodeCompilationError(
                    error_message
                )

    @staticmethod
    def _build_runner_script() -> str:
        return """#!/usr/bin/env bash
set -euo pipefail

/usr/bin/clang++ \
    main.cpp \
    -std=c++17 \
    -O2 \
    -fuse-ld=lld \
    -o main

if [ ! -f tests.json ]; then
    exit 0
fi

/usr/local/bin/python3 - <<'PY'
import json
import subprocess
import sys

with open(
    "tests.json",
    "r",
    encoding="utf-8",
) as file:
    tests = json.load(file)

for test in tests:
    try:
        result = subprocess.run(
            ["./main"],
            input=test["input"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(
            "Program execution timed out after 2 seconds.",
            file=sys.stderr,
        )
        sys.exit(1)

    if result.returncode != 0:
        error_message = result.stderr.strip()

        if not error_message:
            error_message = (
                "Program exited with a non-zero status code."
            )

        print(
            f"Program execution failed:\\n{error_message}",
            file=sys.stderr,
        )
        sys.exit(1)

    actual_output = result.stdout.strip()
    expected_output = test["expected_output"].strip()

    if actual_output != expected_output:
        print(
            "Program output does not match expected output. "
            f"Expected: {expected_output!r}. "
            f"Actual: {actual_output!r}.",
            file=sys.stderr,
        )
        sys.exit(1)
PY
"""
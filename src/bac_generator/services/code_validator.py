import logging
import subprocess
import tempfile
from pathlib import Path

from bac_generator.core.exceptions import CodeCompilationError
from bac_generator.schemas.exercise import ExerciseTestCase

logger = logging.getLogger(__name__)


class CodeValidator:
    def validate_cpp(self, code: str) -> None:
        if not code.strip():
            logger.warning("C++ code validation received empty code.")
            raise CodeCompilationError("Code cannot be empty.")

        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "main.cpp"
            executable_path = Path(temp_dir) / "main"

            source_path.write_text(code, encoding="utf-8")

            logger.info("Starting C++ code compilation.")

            result = subprocess.run(
                [
                    "clang++",
                    str(source_path),
                    "-std=c++17",
                    "-o",
                    str(executable_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_message = result.stderr.strip()

                logger.error(
                    "C++ compilation failed: %s",
                    error_message,
                )

                raise CodeCompilationError(f"Compilation failed:\n{error_message}")

            logger.info("C++ code compiled successfully.")

            try:
                run_result = subprocess.run(
                    [str(executable_path)],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=2,
                )
            except subprocess.TimeoutExpired as exc:
                logger.error("C++ program execution timed out.")

                raise CodeCompilationError("Program execution timed out after 2 seconds.") from exc
            if run_result.returncode != 0:
                error_message = run_result.stderr.strip()

                if not error_message:
                    error_message = "Program exited with a non-zero status code."

                logger.error(
                    "C++ program execution failed: %s",
                    error_message,
                )

                raise CodeCompilationError(f"Program execution failed:\n{error_message}")

    def validate_cpp_with_test_cases(
        self,
        code: str,
        test_cases: list[ExerciseTestCase],
    ) -> None:
        if not code.strip():
            raise CodeCompilationError("Code cannot be empty.")

        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "main.cpp"
            executable_path = Path(temp_dir) / "main"

            source_path.write_text(code, encoding="utf-8")

            compile_result = subprocess.run(
                [
                    "clang++",
                    str(source_path),
                    "-std=c++17",
                    "-o",
                    str(executable_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if compile_result.returncode != 0:
                error_message = compile_result.stderr.strip()

                raise CodeCompilationError(
                    f"Compilation failed:\n{error_message}"
                )

            for test_case in test_cases:
                try:
                    run_result = subprocess.run(
                        [str(executable_path)],
                        input=test_case.input,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=2,
                    )
                except subprocess.TimeoutExpired as exc:
                    raise CodeCompilationError(
                        "Program execution timed out after 2 seconds."
                    ) from exc

                if run_result.returncode != 0:
                    error_message = run_result.stderr.strip()

                    if not error_message:
                        error_message = (
                            "Program exited with a non-zero status code."
                        )

                    raise CodeCompilationError(
                        f"Program execution failed:\n{error_message}"
                    )

                actual_output = run_result.stdout.strip()
                expected_output = test_case.expected_output.strip()

                if actual_output != expected_output:
                    raise CodeCompilationError(
                        "Program output does not match expected output. "
                        f"Expected: {expected_output!r}. "
                        f"Actual: {actual_output!r}."
                    )
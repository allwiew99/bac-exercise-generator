import subprocess
import tempfile
from pathlib import Path

from bac_generator.schemas.exercise import ExerciseTestCase
from bac_generator.schemas.submission import (
    SubmissionEvaluation,
    SubmissionStatus,
)


class SubmissionEvaluator:
    def evaluate(
        self,
        code: str,
        test_cases: list[ExerciseTestCase],
    ) -> SubmissionEvaluation:
        if not code.strip():
            return SubmissionEvaluation(
                score=0,
                passed_tests=0,
                total_tests=len(test_cases),
                status=SubmissionStatus.COMPILATION_ERROR,
                feedback="Codul trimis este gol.",
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "main.cpp"
            executable_path = Path(temp_dir) / "main"

            source_path.write_text(
                code,
                encoding="utf-8",
            )

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

                return SubmissionEvaluation(
                    score=0,
                    passed_tests=0,
                    total_tests=len(test_cases),
                    status=SubmissionStatus.COMPILATION_ERROR,
                    feedback=error_message
                    or "Codul nu a putut fi compilat.",
                )

            passed_tests = 0
            runtime_error = False
            runtime_feedback: str | None = None

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
                except subprocess.TimeoutExpired:
                    runtime_error = True
                    runtime_feedback = (
                        "Programul a depășit limita de timp."
                    )
                    continue

                if run_result.returncode != 0:
                    runtime_error = True

                    error_message = run_result.stderr.strip()

                    runtime_feedback = (
                        error_message
                        or "Programul s-a oprit cu o eroare de execuție."
                    )

                    continue

                actual_output = run_result.stdout.strip()
                expected_output = (
                    test_case.expected_output.strip()
                )

                if actual_output == expected_output:
                    passed_tests += 1

            total_tests = len(test_cases)

            if total_tests == 0:
                return SubmissionEvaluation(
                    score=0,
                    passed_tests=0,
                    total_tests=0,
                    status=SubmissionStatus.FAILED,
                    feedback="Nu există teste disponibile pentru evaluare.",
                )

            score = round(
                passed_tests / total_tests * 100
            )

            if runtime_error and passed_tests == 0:
                status = SubmissionStatus.RUNTIME_ERROR
                feedback = runtime_feedback

            elif passed_tests == total_tests:
                status = SubmissionStatus.PASSED
                feedback = "Toate testele au trecut."

            elif passed_tests == 0:
                status = SubmissionStatus.FAILED
                feedback = "Niciun test nu a trecut."

            else:
                status = SubmissionStatus.PARTIAL
                feedback = (
                    f"{passed_tests} din {total_tests} teste au trecut."
                )

            return SubmissionEvaluation(
                score=score,
                passed_tests=passed_tests,
                total_tests=total_tests,
                status=status,
                feedback=feedback,
            )
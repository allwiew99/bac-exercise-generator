import logging
import subprocess
import tempfile
from pathlib import Path

from bac_generator.core.exceptions import CodeCompilationError

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

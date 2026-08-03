import subprocess
import tempfile
from pathlib import Path


class CodeValidator:
    def validate_cpp(self, code: str) -> None:
        if not code.strip():
            raise ValueError("Code cannot be empty.")

        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "main.cpp"
            executable_path = Path(temp_dir) / "main"

            source_path.write_text(code, encoding="utf-8")

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
                raise ValueError(f"Compilation failed: {result.stderr}")
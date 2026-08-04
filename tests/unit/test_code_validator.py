import pytest

from bac_generator.core.exceptions import CodeCompilationError
from bac_generator.services.code_validator import CodeValidator


def test_validate_cpp_rejects_invalid_code() -> None:
    code_validator = CodeValidator()

    with pytest.raises(CodeCompilationError, match="Compilation failed"):
        code_validator.validate_cpp(
            """
#include <iostream>

int main() {
    std::cout << "ok";
    return 0
}
"""
        )


def test_validate_cpp_accepts_valid_code() -> None:
    code_validator = CodeValidator()

    code_validator.validate_cpp(
        """
#include <iostream>

int main() {
    std::cout << "ok";
    return 0;
}
"""
    )

def test_validate_cpp_rejects_empty_code() -> None:
    code_validator = CodeValidator()

    with pytest.raises(
        CodeCompilationError,
        match="Code cannot be empty",
    ):
        code_validator.validate_cpp("   ")    
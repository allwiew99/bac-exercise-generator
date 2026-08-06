from typing import Protocol


class CodeValidatorProtocol(Protocol):
    def validate_cpp(self, code: str) -> None: ...

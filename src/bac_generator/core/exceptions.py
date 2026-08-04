class BacGeneratorError(Exception):
    """Base exception for application-specific errors."""


class ExerciseValidationError(BacGeneratorError):
    pass


class CodeCompilationError(BacGeneratorError):
    pass


class LLMResponseError(BacGeneratorError):
    pass


class ExerciseGenerationError(BacGeneratorError):
    pass
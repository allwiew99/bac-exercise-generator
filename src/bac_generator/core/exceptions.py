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


class SolutionLockedError(Exception):
    """Raised when the official solution is requested before any submission."""

class RateLimitExceededError(Exception):
    """Raised when a user exceeds an allowed request rate."""
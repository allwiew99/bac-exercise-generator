from typing import Protocol

from bac_generator.schemas.exercise import ExerciseResponse


class LLMClient(Protocol):
    def generate_exercise(self, prompt: str) -> ExerciseResponse:
        ...
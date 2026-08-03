import pytest

from bac_generator.ai.prompt_builder import PromptBuilder
from bac_generator.schemas.exercise import (
    Difficulty,
    ExerciseRequest,
    ExerciseResponse,
)
from bac_generator.services.exercise_service import ExerciseService
from bac_generator.services.exercise_validator import ExerciseValidator


class FakeCodeValidator:
    def validate_cpp(self, code: str) -> None:
        pass


class FakeOllamaClient:
    def generate_exercise(self, prompt: str) -> ExerciseResponse:
        return ExerciseResponse(
            topic="vectori",
            difficulty=Difficulty.MEDIUM,
            statement="Enunț de test.",
            solution="Soluție de test.",
            explanation="Explicație de test.",
        )


class FakeInvalidTopicLLMClient:
    def generate_exercise(self, prompt: str) -> ExerciseResponse:
        return ExerciseResponse(
            topic="matrici",
            difficulty=Difficulty.MEDIUM,
            statement="Enunț de test.",
            solution="Soluție de test.",
            explanation="Explicație de test.",
        )


def test_generate_returns_exercise_response() -> None:
    service = ExerciseService(
        prompt_builder=PromptBuilder(),
        llm_client=FakeOllamaClient(),
        validator=ExerciseValidator(FakeCodeValidator()),
    )

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    response = service.generate(request)

    assert isinstance(response, ExerciseResponse)
    assert response.topic == "vectori"
    assert response.difficulty is Difficulty.MEDIUM
    assert response.statement
    assert response.solution
    assert response.explanation


def test_generate_rejects_exercise_with_mismatched_topic() -> None:
    service = ExerciseService(
        prompt_builder=PromptBuilder(),
        llm_client=FakeInvalidTopicLLMClient(),
        validator=ExerciseValidator(FakeCodeValidator()),
    )

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    with pytest.raises(
        ValueError,
        match="does not match requested topic",
    ):
        service.generate(request)
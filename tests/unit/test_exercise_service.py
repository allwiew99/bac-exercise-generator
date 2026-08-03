from bac_generator.ai.prompt_builder import PromptBuilder
from bac_generator.schemas.exercise import Difficulty, ExerciseRequest, ExerciseResponse
from bac_generator.services.exercise_service import ExerciseService


class FakeOllamaClient:
    def generate_exercise(self, prompt: str) -> ExerciseResponse:
        return ExerciseResponse(
            topic="vectori",
            difficulty=Difficulty.MEDIUM,
            statement="Enunț de test.",
            solution="Soluție de test.",
            explanation="Explicație de test.",
        )


def test_generate_returns_exercise_response() -> None:
    service = ExerciseService(
        prompt_builder=PromptBuilder(),
        llm_client=FakeOllamaClient(),
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
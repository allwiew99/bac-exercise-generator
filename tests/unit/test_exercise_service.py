from bac_generator.schemas.exercise import Difficulty, ExerciseRequest, ExerciseResponse
from bac_generator.services.exercise_service import ExerciseService


def test_generate_returns_exercise_response() -> None:
    service = ExerciseService()

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
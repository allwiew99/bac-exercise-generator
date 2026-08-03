from fastapi.testclient import TestClient

from bac_generator.api.routes.exercises import get_ollama_client
from bac_generator.main import app
from bac_generator.schemas.exercise import Difficulty, ExerciseResponse

client = TestClient(app)


class FakeOllamaClient:
    def generate_exercise(self, prompt: str) -> ExerciseResponse:
        return ExerciseResponse(
            topic="vectori",
            difficulty=Difficulty.MEDIUM,
            statement="Enunț de test.",
            solution="Soluție de test.",
            explanation="Explicație de test.",
        )


def test_generate_exercise_returns_valid_response() -> None:
    app.dependency_overrides[get_ollama_client] = FakeOllamaClient

    try:
        response = client.post(
            "/exercises/generate",
            json={
                "topic": "vectori",
                "difficulty": "medium",
            },
        )

        body = response.json()

        assert response.status_code == 200
        assert body["topic"] == "vectori"
        assert body["difficulty"] == "medium"
        assert body["statement"]
        assert body["solution"]
        assert body["explanation"]
    finally:
        app.dependency_overrides.clear()

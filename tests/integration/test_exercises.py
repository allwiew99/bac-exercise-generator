from fastapi.testclient import TestClient

from bac_generator.api.routes.exercises import (
    get_code_validator,
    get_ollama_client,
)
from bac_generator.core.exceptions import ExerciseGenerationError, LLMResponseError
from bac_generator.main import app
from bac_generator.schemas.exercise import Difficulty, ExerciseResponse

client = TestClient(app)


class FakeCodeValidator:
    def validate_cpp(self, code: str) -> None:
        pass


class FakeExerciseGenerationErrorClient:
    def generate_exercise(self, prompt: str) -> ExerciseResponse:
        raise ExerciseGenerationError("Failed to generate exercise.")

    
class FakeLLMResponseErrorClient:
    def generate_exercise(self, prompt: str) -> ExerciseResponse:
        raise LLMResponseError("Invalid response from LLM.")


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


def test_generate_exercise_returns_exercise_generation_error() -> None:
    app.dependency_overrides[get_ollama_client] = FakeExerciseGenerationErrorClient

    try:
        response = client.post(
            "/exercises/generate",
            json={
                "topic": "vectori",
                "difficulty": "medium",
            },
        )

        body = response.json()

        assert response.status_code == 500
        assert body["error"] == "exercise_generation_error"
        assert "Failed to generate exercise." in body["detail"]
    finally:
        app.dependency_overrides.clear()

def test_generate_exercise_returns_llm_response_error() -> None:
    app.dependency_overrides[get_ollama_client] = FakeLLMResponseErrorClient

    try:
        response = client.post(
            "/exercises/generate",
            json={
                "topic": "vectori",
                "difficulty": "medium",
            },
        )

        body = response.json()

        assert response.status_code == 502
        assert body["error"] == "llm_response_error"
        assert "Invalid response from LLM." in body["detail"]
    finally:
        app.dependency_overrides.clear()

def test_generate_exercise_returns_validation_error() -> None:
    app.dependency_overrides[get_ollama_client] = FakeInvalidTopicLLMClient
    app.dependency_overrides[get_code_validator] = FakeCodeValidator

    try:
        response = client.post(
            "/exercises/generate",
            json={
                "topic": "vectori",
                "difficulty": "medium",
            },
        )

        body = response.json()

        assert response.status_code == 422
        assert body["error"] == "exercise_validation_error"
        assert "does not match requested topic" in body["detail"]
    finally:
        app.dependency_overrides.clear()

def test_generate_exercise_returns_valid_response() -> None:
    app.dependency_overrides[get_ollama_client] = FakeOllamaClient
    app.dependency_overrides[get_code_validator] = FakeCodeValidator

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

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from bac_generator.api.routes.exercises import (
    get_code_validator,
    get_exercise_repository,
    get_llm_client,
)
from bac_generator.core.exceptions import ExerciseGenerationError, LLMResponseError
from bac_generator.db.models import Exercise
from bac_generator.main import app
from bac_generator.schemas.exercise import (
    Difficulty,
    ExerciseResponse,
    ExerciseTestCase,
)

client = TestClient(app)


class FakeCodeValidator:
    def validate_cpp(self, code: str) -> None:
        pass

    def validate_cpp_with_test_cases(
        self,
        code: str,
        test_cases: list[ExerciseTestCase],
    ) -> None:
        pass


class FakeExerciseRepository:
    async def create(
        self,
        exercise_data: ExerciseResponse,
    ) -> Exercise:
        return Exercise(
            topic=exercise_data.topic,
            difficulty=exercise_data.difficulty,
            statement=exercise_data.statement,
            solution=exercise_data.solution,
            explanation=exercise_data.explanation,
            test_cases=[
                {
                    "input": "3\n1 2 4",
                    "expected_output": "6",
                }
            ],
        )

    async def list(self) -> list[Exercise]:
        return [
            Exercise(
                id=1,
                topic="vectori",
                difficulty="medium",
                statement="Enunț 1.",
                solution="Soluție 1.",
                explanation="Explicație 1.",
                created_at=datetime.now(UTC),
                test_cases=[
                    {
                        "input": "3\n1 2 4",
                        "expected_output": "6",
                    }
                ],
            ),
            Exercise(
                id=2,
                topic="matrici",
                difficulty="hard",
                statement="Enunț 2.",
                solution="Soluție 2.",
                explanation="Explicație 2.",
                created_at=datetime.now(UTC),
                test_cases=[
                    {
                        "input": "3\n1 2 4",
                        "expected_output": "6",
                    }
                ],
            ),
        ]

    async def get_by_id(
        self,
        exercise_id: int,
    ) -> Exercise | None:
        if exercise_id == 1:
            return Exercise(
                id=1,
                topic="vectori",
                difficulty="medium",
                statement="Enunț 1.",
                solution="Soluție 1.",
                explanation="Explicație 1.",
                created_at=datetime.now(UTC),
                test_cases=[
                    {
                        "input": "3\n1 2 4",
                        "expected_output": "6",
                    }
                ],
            )

        return None


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
            test_cases=[
                ExerciseTestCase(
                    input="3\n1 2 4",
                    expected_output="6",
                )
            ],
        )


class FakeInvalidTopicLLMClient:
    def generate_exercise(self, prompt: str) -> ExerciseResponse:
        return ExerciseResponse(
            topic="matrici",
            difficulty=Difficulty.MEDIUM,
            statement="Enunț de test.",
            solution="Soluție de test.",
            explanation="Explicație de test.",
            test_cases=[
                ExerciseTestCase(
                    input="3\n1 2 4",
                    expected_output="6",
                )
            ],
        )


def test_generate_exercise_returns_exercise_generation_error() -> None:
    app.dependency_overrides[get_llm_client] = FakeExerciseGenerationErrorClient

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
    app.dependency_overrides[get_llm_client] = FakeLLMResponseErrorClient

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
    app.dependency_overrides[get_llm_client] = FakeInvalidTopicLLMClient
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
    app.dependency_overrides[get_llm_client] = FakeOllamaClient
    app.dependency_overrides[get_code_validator] = FakeCodeValidator
    app.dependency_overrides[get_exercise_repository] = FakeExerciseRepository

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


def test_list_exercises_returns_exercises() -> None:
    app.dependency_overrides[get_exercise_repository] = FakeExerciseRepository

    try:
        response = client.get("/exercises/")

        body = response.json()

        assert response.status_code == 200
        assert isinstance(body, list)
        assert len(body) == 2
        assert body[0]["id"] == 1
        assert body[0]["topic"] == "vectori"
        assert body[0]["difficulty"] == "medium"
        assert body[0]["statement"] == "Enunț 1."
        assert body[0]["solution"] == "Soluție 1."
        assert body[0]["explanation"] == "Explicație 1."
        assert "created_at" in body[0]
        assert body[1]["id"] == 2
        assert body[1]["topic"] == "matrici"
        assert body[1]["difficulty"] == "hard"
    finally:
        app.dependency_overrides.clear()


def test_get_exercise_by_id_returns_existing_exercise() -> None:
    app.dependency_overrides[get_exercise_repository] = FakeExerciseRepository

    try:
        response = client.get("/exercises/1")

        body = response.json()

        assert response.status_code == 200
        assert body["id"] == 1
        assert body["topic"] == "vectori"
        assert body["difficulty"] == "medium"

        assert "created_at" in body
    finally:
        app.dependency_overrides.clear()


def test_get_exercise_by_id_returns_404_for_missing_exercise() -> None:
    app.dependency_overrides[get_exercise_repository] = FakeExerciseRepository

    try:
        response = client.get("/exercises/999999")

        body = response.json()

        assert response.status_code == 404
        assert body["detail"] == "Exercise not found."
    finally:
        app.dependency_overrides.clear()

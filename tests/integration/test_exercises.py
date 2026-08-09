from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from bac_generator.api.dependencies.auth import (
    CurrentUser,
    get_current_user,
)
from bac_generator.api.routes.exercises import (
    get_code_validator,
    get_exercise_repository,
    get_llm_client,
    get_rate_limiter,
    get_submission_evaluator,
    get_submission_repository,
)
from bac_generator.core.exceptions import (
    ExerciseGenerationError,
    LLMResponseError,
)
from bac_generator.db.models import Exercise, Submission
from bac_generator.main import app
from bac_generator.schemas.exercise import (
    Difficulty,
    ExerciseResponse,
    ExerciseTestCase,
)
from bac_generator.schemas.submission import (
    SubmissionCreate,
    SubmissionEvaluation,
    SubmissionProgress,
    SubmissionStatus,
)


def get_fake_current_user() -> CurrentUser:
    return CurrentUser(
        uid="test-user-123",
        email="test@example.com",
    )


@pytest.fixture(autouse=True)
def override_current_user() -> Generator[None, None, None]:
    app.dependency_overrides[get_current_user] = get_fake_current_user

    yield

    app.dependency_overrides.pop(get_current_user, None)


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


class FakeBlockedRateLimiter:
    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> bool:
        return False
    

class FakeExerciseRepository:
    async def create(
        self,
        exercise_data: ExerciseResponse,
        user_id: str,
    ) -> Exercise:
        return Exercise(
            id=1,
            user_id=user_id,
            topic=exercise_data.topic,
            difficulty=exercise_data.difficulty,
            statement=exercise_data.statement,
            solution=exercise_data.solution,
            explanation=exercise_data.explanation,
            created_at=datetime.now(UTC),
            test_cases=[
                test_case.model_dump()
                for test_case in exercise_data.test_cases
            ],
        )

    async def list(
        self,
        user_id: str,
    ) -> list[Exercise]:
        return [
            Exercise(
                id=1,
                user_id=user_id,
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
                user_id=user_id,
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
        user_id: str,
    ) -> Exercise | None:
        if exercise_id == 1:
            return Exercise(
                id=1,
                user_id=user_id,
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


class FakeSubmissionRepository:
    async def create(
        self,
        submission_data: SubmissionCreate,
    ) -> Submission:
        return Submission(
            id=1,
            exercise_id=submission_data.exercise_id,
            user_id=submission_data.user_id,
            code=submission_data.code,
            score=submission_data.score,
            passed_tests=submission_data.passed_tests,
            total_tests=submission_data.total_tests,
            status=submission_data.status,
            feedback=submission_data.feedback,
            created_at=datetime.now(UTC),
        )

    async def get_latest_for_exercise(
        self,
        exercise_id: int,
        user_id: str,
    ) -> Submission | None:
        return None

    async def list_for_exercise(
        self,
        exercise_id: int,
        user_id: str,
    ) -> list[Submission]:
        return []

        async def get_progress_for_exercise(
            self,
            exercise_id: int,
            user_id: str,
        ) -> SubmissionProgress:
            return SubmissionProgress(
                has_submitted=False,
                latest_score=None,
                submission_count=0,
                completed=False,
            )

    async def get_progress_for_exercises(
        self,
        exercise_ids: list[int],
        user_id: str,
    ) -> dict[int, SubmissionProgress]:
        return {
            exercise_id: SubmissionProgress(
                has_submitted=False,
                latest_score=None,
                submission_count=0,
                completed=False,
            )
            for exercise_id in exercise_ids
        }

    async def get_progress_for_exercise(
        self,
        exercise_id: int,
        user_id: str,
    ) -> SubmissionProgress:
        return SubmissionProgress(
            has_submitted=False,
            latest_score=None,
            submission_count=0,
            completed=False,
        )


class FakeSubmissionRepositoryWithExistingSubmission(
    FakeSubmissionRepository
):
    async def get_latest_for_exercise(
        self,
        exercise_id: int,
        user_id: str,
    ) -> Submission | None:
        return Submission(
            id=1,
            exercise_id=exercise_id,
            user_id=user_id,
            code="#include <iostream>\nint main() { return 0; }",
            score=75,
            passed_tests=3,
            total_tests=4,
            status=SubmissionStatus.PARTIAL,
            feedback="3 din 4 teste au trecut.",
            created_at=datetime.now(UTC),
        )


class FakeSubmissionEvaluator:
    def evaluate(
        self,
        code: str,
        test_cases: list[ExerciseTestCase],
    ) -> SubmissionEvaluation:
        return SubmissionEvaluation(
            score=75,
            passed_tests=3,
            total_tests=4,
            status=SubmissionStatus.PARTIAL,
            feedback="3 din 4 teste au trecut.",
        )


class FakeExerciseGenerationErrorClient:
    def generate_exercise(
        self,
        prompt: str,
    ) -> ExerciseResponse:
        raise ExerciseGenerationError(
            "Failed to generate exercise."
        )


class FakeLLMResponseErrorClient:
    def generate_exercise(
        self,
        prompt: str,
    ) -> ExerciseResponse:
        raise LLMResponseError(
            "Invalid response from LLM."
        )


class FakeOllamaClient:
    def generate_exercise(
        self,
        prompt: str,
    ) -> ExerciseResponse:
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
                    is_hidden=False,
                ),
                ExerciseTestCase(
                    input="2\n5 5",
                    expected_output="10",
                    is_hidden=True,
                ),
                ExerciseTestCase(
                    input="1\n7",
                    expected_output="7",
                    is_hidden=True,
                ),
                ExerciseTestCase(
                    input="4\n1 1 1 1",
                    expected_output="4",
                    is_hidden=True,
                ),
            ],
        )


class FakeInvalidTopicLLMClient:
    def generate_exercise(
        self,
        prompt: str,
    ) -> ExerciseResponse:
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
    app.dependency_overrides[get_llm_client] = (
        FakeExerciseGenerationErrorClient
    )

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
    app.dependency_overrides[get_llm_client] = (
        FakeLLMResponseErrorClient
    )

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
    app.dependency_overrides[get_llm_client] = (
        FakeInvalidTopicLLMClient
    )
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


def test_generate_exercise_returns_safe_response() -> None:
    app.dependency_overrides[get_llm_client] = FakeOllamaClient
    app.dependency_overrides[get_code_validator] = FakeCodeValidator
    app.dependency_overrides[get_exercise_repository] = (
        FakeExerciseRepository
    )

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
        assert body["id"] == 1
        assert body["topic"] == "vectori"
        assert body["difficulty"] == "medium"
        assert body["statement"]
        assert "created_at" in body

        assert "solution" not in body
        assert "explanation" not in body
        assert body["sample_test_cases"] == [
            {
                "input": "3\n1 2 4",
                "expected_output": "6",
            }
        ]
        assert "test_cases" not in body

    finally:
        app.dependency_overrides.clear()


def test_list_exercises_returns_safe_exercises() -> None:
    app.dependency_overrides[get_exercise_repository] = (
        FakeExerciseRepository
    )
    app.dependency_overrides[get_submission_repository] = (
        FakeSubmissionRepository
    )

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
        assert "created_at" in body[0]

        assert "solution" not in body[0]
        assert "explanation" not in body[0]
        assert "test_cases" not in body[0]

        assert body[1]["id"] == 2
        assert body[1]["topic"] == "matrici"
        assert body[1]["difficulty"] == "hard"

        assert "solution" not in body[1]
        assert "explanation" not in body[1]
        assert "test_cases" not in body[1]

    finally:
        app.dependency_overrides.clear()


def test_get_exercise_by_id_returns_safe_exercise() -> None:
    app.dependency_overrides[get_exercise_repository] = (
        FakeExerciseRepository
    )
    app.dependency_overrides[get_submission_repository] = (
        FakeSubmissionRepository
    )

    try:
        response = client.get("/exercises/1")

        body = response.json()

        assert response.status_code == 200
        assert body["id"] == 1
        assert body["topic"] == "vectori"
        assert body["difficulty"] == "medium"
        assert body["statement"] == "Enunț 1."
        assert "created_at" in body

        assert "solution" not in body
        assert "explanation" not in body
        assert "test_cases" not in body

    finally:
        app.dependency_overrides.clear()


def test_get_exercise_by_id_returns_404_for_missing_exercise() -> None:
    app.dependency_overrides[get_exercise_repository] = (
        FakeExerciseRepository
    )

    try:
        response = client.get("/exercises/999999")

        body = response.json()

        assert response.status_code == 404
        assert body["detail"] == "Exercise not found."

    finally:
        app.dependency_overrides.clear()


def test_submit_solution_returns_submission_result() -> None:
    app.dependency_overrides[get_exercise_repository] = (
        FakeExerciseRepository
    )
    app.dependency_overrides[get_submission_repository] = (
        FakeSubmissionRepository
    )
    app.dependency_overrides[get_submission_evaluator] = (
        FakeSubmissionEvaluator
    )

    try:
        response = client.post(
            "/exercises/1/submissions",
            json={
                "code": (
                    "#include <iostream>\n"
                    "int main() { return 0; }"
                )
            },
        )

        body = response.json()

        assert response.status_code == 200
        assert body["id"] == 1
        assert body["exercise_id"] == 1
        assert body["score"] == 75
        assert body["passed_tests"] == 3
        assert body["total_tests"] == 4
        assert body["status"] == "partial"
        assert body["feedback"] == "3 din 4 teste au trecut."
        assert "created_at" in body

        assert "user_id" not in body
        assert "code" not in body

    finally:
        app.dependency_overrides.clear()


def test_submit_solution_returns_404_for_missing_exercise() -> None:
    app.dependency_overrides[get_exercise_repository] = (
        FakeExerciseRepository
    )
    app.dependency_overrides[get_submission_repository] = (
        FakeSubmissionRepository
    )
    app.dependency_overrides[get_submission_evaluator] = (
        FakeSubmissionEvaluator
    )

    try:
        response = client.post(
            "/exercises/999999/submissions",
            json={
                "code": (
                    "#include <iostream>\n"
                    "int main() { return 0; }"
                )
            },
        )

        body = response.json()

        assert response.status_code == 404
        assert body["detail"] == "Exercise not found."

    finally:
        app.dependency_overrides.clear()


def test_get_official_solution_returns_403_without_submission() -> None:
    app.dependency_overrides[get_exercise_repository] = (
        FakeExerciseRepository
    )
    app.dependency_overrides[get_submission_repository] = (
        FakeSubmissionRepository
    )

    try:
        response = client.get(
            "/exercises/1/solution"
        )

        body = response.json()

        assert response.status_code == 403
        assert body["error"] == "solution_locked"
        assert (
            "Official solution is available only after submitting a solution."
            in body["detail"]
        )

    finally:
        app.dependency_overrides.clear()


def test_get_official_solution_returns_solution_after_submission() -> None:
    app.dependency_overrides[get_exercise_repository] = (
        FakeExerciseRepository
    )
    app.dependency_overrides[get_submission_repository] = (
        FakeSubmissionRepositoryWithExistingSubmission
    )

    try:
        response = client.get(
            "/exercises/1/solution"
        )

        body = response.json()

        assert response.status_code == 200
        assert body["solution"] == "Soluție 1."
        assert body["explanation"] == "Explicație 1."

    finally:
        app.dependency_overrides.clear()


def test_get_official_solution_returns_404_for_missing_exercise() -> None:
    app.dependency_overrides[get_exercise_repository] = (
        FakeExerciseRepository
    )
    app.dependency_overrides[get_submission_repository] = (
        FakeSubmissionRepositoryWithExistingSubmission
    )

    try:
        response = client.get(
            "/exercises/999999/solution"
        )

        body = response.json()

        assert response.status_code == 404
        assert body["detail"] == "Exercise not found."

    finally:
        app.dependency_overrides.clear()


def test_generate_exercise_returns_429_when_rate_limited() -> None:
    app.dependency_overrides[get_rate_limiter] = FakeBlockedRateLimiter

    try:
        response = client.post(
            "/exercises/generate",
            json={
                "topic": "vectori",
                "difficulty": "medium",
            },
        )

        body = response.json()

        assert response.status_code == 429
        assert body["error"] == "rate_limit_exceeded"
        assert (
            "Too many exercise generation requests"
            in body["detail"]
        )

    finally:
        app.dependency_overrides.clear()


def test_submit_solution_returns_429_when_rate_limited() -> None:
    app.dependency_overrides[get_rate_limiter] = FakeBlockedRateLimiter

    try:
        response = client.post(
            "/exercises/1/submissions",
            json={
                "code": (
                    "#include <iostream>\n"
                    "int main() { return 0; }"
                )
            },
        )

        body = response.json()

        assert response.status_code == 429
        assert body["error"] == "rate_limit_exceeded"
        assert "Too many submission requests" in body["detail"]

    finally:
        app.dependency_overrides.clear()
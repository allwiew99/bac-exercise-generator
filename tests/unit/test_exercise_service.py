from datetime import UTC, datetime

import pytest

from bac_generator.ai.prompt_builder import PromptBuilder
from bac_generator.core.exceptions import ExerciseValidationError
from bac_generator.db.models import Exercise
from bac_generator.schemas.exercise import (
    Difficulty,
    ExerciseRequest,
    ExerciseResponse,
    ExerciseTestCase,
)
from bac_generator.services.exercise_service import ExerciseService
from bac_generator.services.exercise_validator import ExerciseValidator

TEST_USER_ID = "test-user-123"


class FakeCodeValidator:
    def validate_cpp(self, code: str) -> None:
        pass

    def validate_cpp_with_test_cases(
        self,
        code: str,
        test_cases: list[ExerciseTestCase],
    ) -> None:
        pass


class FakeRetryLLMClient:
    def __init__(self) -> None:
        self.calls = 0

    def generate_exercise(
        self,
        prompt: str,
    ) -> ExerciseResponse:
        self.calls += 1

        if self.calls == 1:
            raise ExerciseValidationError(
                "Temporary validation failure."
            )

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


class FakeAlwaysFailLLMClient:
    def __init__(self) -> None:
        self.calls = 0

    def generate_exercise(
        self,
        prompt: str,
    ) -> ExerciseResponse:
        self.calls += 1

        raise ExerciseValidationError(
            "Temporary validation failure."
        )


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
            test_cases=[
                test_case.model_dump()
                for test_case in exercise_data.test_cases
            ],
            created_at=datetime.now(UTC),
        )

    async def get_by_id(
        self,
        exercise_id: int,
        user_id: str,
    ) -> Exercise | None:
        return None

    async def list(
        self,
        user_id: str,
    ) -> list[Exercise]:
        return []


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


async def test_generate_returns_persisted_exercise() -> None:
    service = ExerciseService(
        prompt_builder=PromptBuilder(),
        llm_client=FakeOllamaClient(),
        validator=ExerciseValidator(
            FakeCodeValidator()
        ),
        repository=FakeExerciseRepository(),
    )

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    exercise = await service.generate(
        request,
        TEST_USER_ID,
    )

    assert isinstance(exercise, Exercise)
    assert exercise.id == 1
    assert exercise.user_id == TEST_USER_ID
    assert exercise.topic == "vectori"
    assert exercise.difficulty == Difficulty.MEDIUM
    assert exercise.statement
    assert exercise.solution
    assert exercise.explanation
    assert exercise.created_at is not None


async def test_generate_rejects_exercise_with_mismatched_topic() -> None:
    service = ExerciseService(
        prompt_builder=PromptBuilder(),
        llm_client=FakeInvalidTopicLLMClient(),
        validator=ExerciseValidator(
            FakeCodeValidator()
        ),
        repository=FakeExerciseRepository(),
    )

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    with pytest.raises(
        ExerciseValidationError,
        match="does not match requested topic",
    ):
        await service.generate(
            request,
            TEST_USER_ID,
        )


async def test_generate_retries_after_validation_error() -> None:
    llm_client = FakeRetryLLMClient()

    service = ExerciseService(
        prompt_builder=PromptBuilder(),
        llm_client=llm_client,
        validator=ExerciseValidator(
            FakeCodeValidator()
        ),
        repository=FakeExerciseRepository(),
    )

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    exercise = await service.generate(
        request,
        TEST_USER_ID,
    )

    assert exercise.topic == "vectori"
    assert exercise.user_id == TEST_USER_ID
    assert llm_client.calls == 2


async def test_generate_raises_after_max_attempts() -> None:
    llm_client = FakeAlwaysFailLLMClient()

    service = ExerciseService(
        prompt_builder=PromptBuilder(),
        llm_client=llm_client,
        validator=ExerciseValidator(
            FakeCodeValidator()
        ),
        repository=FakeExerciseRepository(),
    )

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    with pytest.raises(ExerciseValidationError):
        await service.generate(
            request,
            TEST_USER_ID,
        )

    assert llm_client.calls == 3
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


class FakeCodeValidator:
    def validate_cpp(self, code: str) -> None:
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
            raise ExerciseValidationError("Temporary validation failure.")

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


class FakeAlwaysFailLLMClient:
    def __init__(self) -> None:
        self.calls = 0

    def generate_exercise(
        self,
        prompt: str,
    ) -> ExerciseResponse:
        self.calls += 1
        raise ExerciseValidationError("Temporary validation failure.")


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
        )

    async def get_by_id(
        self,
        exercise_id: int,
    ) -> Exercise | None:
        return None

    async def list(self) -> list[Exercise]:
        return []


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


async def test_generate_returns_exercise_response() -> None:
    service = ExerciseService(
        prompt_builder=PromptBuilder(),
        llm_client=FakeOllamaClient(),
        validator=ExerciseValidator(FakeCodeValidator()),
        repository=FakeExerciseRepository(),
    )

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    response = await service.generate(request)

    assert isinstance(response, ExerciseResponse)
    assert response.topic == "vectori"
    assert response.difficulty is Difficulty.MEDIUM
    assert response.statement
    assert response.solution
    assert response.explanation


async def test_generate_rejects_exercise_with_mismatched_topic() -> None:
    service = ExerciseService(
        prompt_builder=PromptBuilder(),
        llm_client=FakeInvalidTopicLLMClient(),
        validator=ExerciseValidator(FakeCodeValidator()),
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
        await service.generate(request)


async def test_generate_retries_after_validation_error() -> None:
    llm_client = FakeRetryLLMClient()

    service = ExerciseService(
        prompt_builder=PromptBuilder(),
        llm_client=llm_client,
        validator=ExerciseValidator(FakeCodeValidator()),
        repository=FakeExerciseRepository(),
    )

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    response = await service.generate(request)

    assert response.topic == "vectori"
    assert llm_client.calls == 2


async def test_generate_raises_after_max_attempts() -> None:
    llm_client = FakeAlwaysFailLLMClient()

    service = ExerciseService(
        prompt_builder=PromptBuilder(),
        llm_client=llm_client,
        validator=ExerciseValidator(FakeCodeValidator()),
        repository=FakeExerciseRepository(),
    )

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    with pytest.raises(ExerciseValidationError):
        await service.generate(request)

    assert llm_client.calls == 3

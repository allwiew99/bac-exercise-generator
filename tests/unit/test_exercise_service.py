from datetime import UTC, datetime
from typing import Protocol

import pytest

from bac_generator.ai.llm_client import LLMClient
from bac_generator.ai.prompt_builder import PromptBuilder
from bac_generator.core.exceptions import ExerciseValidationError
from bac_generator.db.models import Exercise
from bac_generator.schemas.exercise import (
    Difficulty,
    ExerciseRequest,
    ExerciseResponse,
    ExerciseTestCase,
)
from bac_generator.schemas.retrieval import RetrievedChunk
from bac_generator.services.exercise_service import ExerciseService
from bac_generator.services.exercise_validator import ExerciseValidator
from bac_generator.services.rag_context_provider import (
    RagContext,
    RagContextProviderProtocol,
)

TEST_USER_ID = "test-user-123"
VALID_CPP_SOLUTION = "int main() { return 0; }"


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
            solution=VALID_CPP_SOLUTION,
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
    def __init__(self) -> None:
        self.last_prompt = ""

    def generate_exercise(
        self,
        prompt: str,
    ) -> ExerciseResponse:
        self.last_prompt = prompt
        return ExerciseResponse(
            topic="vectori",
            difficulty=Difficulty.MEDIUM,
            statement="Enunț de test.",
            solution=VALID_CPP_SOLUTION,
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
            solution=VALID_CPP_SOLUTION,
            explanation="Explicație de test.",
            test_cases=[
                ExerciseTestCase(
                    input="3\n1 2 4",
                    expected_output="6",
                )
            ],
        )


class FakeRagContextProvider:
    def __init__(
        self,
        context: str = "",
        chunks: list[RetrievedChunk] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.context = context
        self.chunks = chunks or []
        self.error = error
        self.calls: list[tuple[str, str | None, str | None]] = []

    async def get_context(
        self,
        query: str,
        topic: str | None = None,
        difficulty: str | None = None,
    ) -> RagContext:
        self.calls.append((query, topic, difficulty))
        if self.error is not None:
            raise self.error
        return RagContext(text=self.context, chunks=self.chunks)


class NoveltyValidatorProtocol(Protocol):
    def validate(
        self,
        exercise: ExerciseResponse,
        references: list[RetrievedChunk],
    ) -> None:
        ...


class FakeNoveltyValidator:
    def __init__(self, reject_first: bool = False) -> None:
        self.reject_first = reject_first
        self.calls: list[tuple[str, list[RetrievedChunk]]] = []

    def validate(
        self,
        exercise: ExerciseResponse,
        references: list[RetrievedChunk],
    ) -> None:
        self.calls.append((exercise.statement, references))
        if self.reject_first and len(self.calls) == 1:
            raise ExerciseValidationError(
                "The generated statement is too similar to reference ref-1."
            )


class FakeNoveltyRetryLLMClient(FakeOllamaClient):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def generate_exercise(self, prompt: str) -> ExerciseResponse:
        self.calls += 1
        response = super().generate_exercise(prompt)
        return response.model_copy(
            update={"statement": f"Enunț încercarea {self.calls}."}
        )


def _rag_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        id="ref-1",
        text="Conținut de referință.",
        source="subject.pdf",
        topic="arrays",
        score=0.9,
    )


def _build_service(
    llm_client: LLMClient,
    *,
    rag_context_provider: RagContextProviderProtocol | None = None,
    novelty_validator: NoveltyValidatorProtocol | None = None,
) -> ExerciseService:
    return ExerciseService(
        prompt_builder=PromptBuilder(),
        llm_client=llm_client,
        validator=ExerciseValidator(FakeCodeValidator()),
        repository=FakeExerciseRepository(),
        rag_context_provider=(
            rag_context_provider or FakeRagContextProvider()
        ),
        novelty_validator=(novelty_validator or FakeNoveltyValidator()),
    )


async def test_generate_returns_persisted_exercise() -> None:
    service = _build_service(FakeOllamaClient())

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
    service = _build_service(FakeInvalidTopicLLMClient())

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

    service = _build_service(llm_client)

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

    service = _build_service(llm_client)

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    with pytest.raises(ExerciseValidationError):
        await service.generate(
            request,
            TEST_USER_ID,
        )

    assert llm_client.calls == 6


async def test_generate_includes_successful_rag_context() -> None:
    rag_context_provider = FakeRagContextProvider(
        context="FAKE RAG CONTEXT"
    )
    llm_client = FakeOllamaClient()
    service = _build_service(
        llm_client,
        rag_context_provider=rag_context_provider,
    )
    request = ExerciseRequest(topic="vectori", difficulty=Difficulty.MEDIUM)

    exercise = await service.generate(request, TEST_USER_ID)

    assert exercise.topic == "vectori"
    assert len(rag_context_provider.calls) == 1
    query, topic, difficulty = rag_context_provider.calls[0]
    assert "vectori" in query
    assert topic == "vectori"
    assert difficulty == Difficulty.MEDIUM
    assert "Reference context from validated" in llm_client.last_prompt
    assert "FAKE RAG CONTEXT" in llm_client.last_prompt


async def test_generate_uses_empty_context_returned_by_fail_open_provider() -> None:
    rag_context_provider = FakeRagContextProvider()
    llm_client = FakeOllamaClient()
    service = _build_service(
        llm_client,
        rag_context_provider=rag_context_provider,
    )
    request = ExerciseRequest(topic="vectori", difficulty=Difficulty.MEDIUM)

    exercise = await service.generate(request, TEST_USER_ID)

    assert exercise.topic == "vectori"
    assert len(rag_context_provider.calls) == 1
    assert "Reference context from validated" not in llm_client.last_prompt
    assert "FAKE RAG CONTEXT" not in llm_client.last_prompt


async def test_generate_does_not_swallow_fail_closed_provider_error() -> None:
    rag_context_provider = FakeRagContextProvider(
        error=RuntimeError("RAG fail-closed error")
    )
    service = _build_service(
        FakeOllamaClient(),
        rag_context_provider=rag_context_provider,
    )
    request = ExerciseRequest(topic="vectori", difficulty=Difficulty.MEDIUM)

    with pytest.raises(RuntimeError, match="RAG fail-closed error"):
        await service.generate(request, TEST_USER_ID)


async def test_generate_passes_ordered_references_to_novelty_validator() -> None:
    references = [_rag_chunk()]
    novelty_validator = FakeNoveltyValidator()
    service = _build_service(
        FakeOllamaClient(),
        rag_context_provider=FakeRagContextProvider(
            context="FAKE RAG CONTEXT",
            chunks=references,
        ),
        novelty_validator=novelty_validator,
    )

    await service.generate(
        ExerciseRequest(topic="vectori", difficulty=Difficulty.MEDIUM),
        TEST_USER_ID,
    )

    assert novelty_validator.calls == [("Enunț de test.", references)]


async def test_novelty_rejection_uses_existing_repair_retry_flow() -> None:
    llm_client = FakeNoveltyRetryLLMClient()
    novelty_validator = FakeNoveltyValidator(reject_first=True)
    service = _build_service(
        llm_client,
        rag_context_provider=FakeRagContextProvider(
            context="FAKE RAG CONTEXT",
            chunks=[_rag_chunk()],
        ),
        novelty_validator=novelty_validator,
    )

    exercise = await service.generate(
        ExerciseRequest(topic="vectori", difficulty=Difficulty.MEDIUM),
        TEST_USER_ID,
    )

    assert exercise.statement == "Enunț încercarea 2."
    assert llm_client.calls == 2
    assert len(novelty_validator.calls) == 2
    assert "too similar" in llm_client.last_prompt
    assert "FAKE RAG CONTEXT" in llm_client.last_prompt

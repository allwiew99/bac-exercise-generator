import asyncio
import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from typing import Any, Protocol, cast
from uuid import uuid4

from pinecone import Pinecone
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.sql.dml import Delete

from bac_generator.ai.embeddings.vertex_embedding_client import (
    VertexEmbeddingClient,
)
from bac_generator.ai.gemini_client import GeminiClient
from bac_generator.ai.llm_client import LLMClient
from bac_generator.ai.prompt_builder import PromptBuilder
from bac_generator.ai.retrieval.context_builder import ContextBuilder
from bac_generator.core.config import settings
from bac_generator.db.models import Exercise
from bac_generator.db.session import session_factory
from bac_generator.evaluation.rag.novelty import (
    ReferenceSimilarity,
    find_highest_reference_similarity,
)
from bac_generator.repositories.exercise_repository import ExerciseRepository
from bac_generator.repositories.pinecone_repository import PineconeRepository
from bac_generator.repositories.vector_repository_protocol import VectorMetadata
from bac_generator.schemas.exercise import (
    Difficulty,
    ExerciseRequest,
    ExerciseResponse,
    ExerciseTestCase,
)
from bac_generator.schemas.retrieval import RetrievedChunk
from bac_generator.services.code_runner_protocol import CodeRunnerProtocol
from bac_generator.services.code_validator import CodeValidator
from bac_generator.services.exercise_novelty_validator import (
    ExerciseNoveltyValidator,
)
from bac_generator.services.exercise_service import ExerciseService
from bac_generator.services.exercise_validator import ExerciseValidator
from bac_generator.services.local_code_runner import LocalCodeRunner
from bac_generator.services.rag_context_provider import (
    RagContextProvider,
    RerankerProtocol,
    RetrievalServiceProtocol,
)
from bac_generator.services.retrieval_service import RetrievalService
from bac_generator.services.sandbox_code_runner import SandboxCodeRunner

logger = logging.getLogger(__name__)

EXPECTED_VECTOR_COUNT = 317
EXPECTED_DIMENSION = 768
EXPECTED_METRIC = "cosine"
CONTEXT_TOP_K = 5
CASE_COOLDOWN_SECONDS = 5


class GenerationCase(BaseModel):
    id: str
    topic: str
    difficulty: Difficulty


class RetrievedDocumentTrace(BaseModel):
    id: str
    score: float
    topic: str
    source: str
    year: int | None


class CodeExecutionTrace(BaseModel):
    configured_provider: str
    runner: str
    sandbox_used: bool
    calls: int
    result: str
    error: str | None


class GenerationCaseResult(BaseModel):
    case_id: str
    requested_topic: str
    requested_difficulty: Difficulty
    retrieval_service_called: bool
    retrieved_documents: list[RetrievedDocumentTrace]
    initial_filtered_result_count: int
    filtered_retrieval_succeeded: bool
    semantic_fallback_triggered: bool
    context_chunk_count: int
    context_chunk_ids: list[str]
    pinecone_order_preserved: bool
    prompt_context_non_empty: bool
    generation_attempts: int
    generation_success: bool
    validator_result: str
    code_execution: CodeExecutionTrace
    persisted_exercise_id: int | None
    generated_statement: str | None
    highest_reference_similarity: ReferenceSimilarity | None
    elapsed_ms: float
    error: str | None


class FailOpenValidationResult(BaseModel):
    fail_open_generation_succeeded: bool
    fail_open_empty_context_used: bool
    fail_open_failure_logged: bool
    fail_open_validator_result: str
    fail_open_code_execution: CodeExecutionTrace
    fail_open_persisted_exercise_id: int | None
    fail_closed_error_propagated: bool
    fail_closed_gemini_calls: int
    fail_closed_error: str | None


class IndexSnapshot(BaseModel):
    index_name: str
    namespace: str
    dimension: int
    metric: str
    namespace_vector_count: int
    total_vector_count: int
    namespaces: list[str]


class RerankerTrace(BaseModel):
    configured_enabled: bool
    construction_attempts: int
    discovery_engine_used: bool


class PersistenceCleanupResult(BaseModel):
    inserted_count: int
    deleted_count: int
    remaining_rows: int
    cleanup_completed: bool
    cleanup_sql: str


class PersistenceTrace(PersistenceCleanupResult):
    validation_user_id: str
    inserted_ids: list[int]


class GenerationE2EReport(BaseModel):
    generated_at: datetime
    index: IndexSnapshot
    cases: list[GenerationCaseResult]
    successful_cases: int
    failed_cases: int
    fallback_cases: int
    suspicious_novelty_cases: int
    fail_open_validation: FailOpenValidationResult
    reranker: RerankerTrace
    persistence: PersistenceTrace
    code_runner_limitation: str | None
    safe_for_production_deployment: bool


class CleanupSessionProtocol(Protocol):
    async def scalar(self, statement: Any) -> int | None:
        ...

    async def execute(self, statement: Any) -> Any:
        ...

    async def commit(self) -> None:
        ...


CleanupSessionFactory = Callable[
    [],
    AbstractAsyncContextManager[CleanupSessionProtocol],
]


DEFAULT_CASES = [
    GenerationCase(
        id="pseudocode-medium",
        topic="pseudocode",
        difficulty=Difficulty.MEDIUM,
    ),
    GenerationCase(id="arrays-easy", topic="arrays", difficulty=Difficulty.EASY),
    GenerationCase(
        id="matrices-medium",
        topic="matrices",
        difficulty=Difficulty.MEDIUM,
    ),
    GenerationCase(id="files-hard", topic="files", difficulty=Difficulty.HARD),
    GenerationCase(
        id="graphs-medium",
        topic="graphs",
        difficulty=Difficulty.MEDIUM,
    ),
    GenerationCase(
        id="number-processing-easy",
        topic="number processing",
        difficulty=Difficulty.EASY,
    ),
    GenerationCase(
        id="subprograms-hard",
        topic="subprograms",
        difficulty=Difficulty.HARD,
    ),
    GenerationCase(
        id="binary-search-medium",
        topic="binary search",
        difficulty=Difficulty.MEDIUM,
    ),
]


def create_validation_user_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"__rag_e2e_validation__{timestamp}-{uuid4().hex[:12]}"


def validation_cleanup_statement(validation_user_id: str) -> Delete:
    return delete(Exercise).where(Exercise.user_id == validation_user_id)


def build_validation_cleanup_sql(validation_user_id: str) -> str:
    escaped_user_id = validation_user_id.replace("'", "''")
    return (
        "DELETE FROM exercises WHERE user_id = "
        f"'{escaped_user_id}';"
    )


async def cleanup_validation_rows(
    validation_user_id: str,
    *,
    session_factory_override: CleanupSessionFactory | None = None,
) -> PersistenceCleanupResult:
    factory = session_factory_override or cast(
        CleanupSessionFactory,
        session_factory,
    )
    count_statement = (
        select(func.count())
        .select_from(Exercise)
        .where(Exercise.user_id == validation_user_id)
    )

    async with factory() as session:
        inserted_count = int(await session.scalar(count_statement) or 0)
        await session.execute(validation_cleanup_statement(validation_user_id))
        await session.commit()
        remaining_rows = int(await session.scalar(count_statement) or 0)

    return PersistenceCleanupResult(
        inserted_count=inserted_count,
        deleted_count=max(0, inserted_count - remaining_rows),
        remaining_rows=remaining_rows,
        cleanup_completed=remaining_rows == 0,
        cleanup_sql=build_validation_cleanup_sql(validation_user_id),
    )


def finalize_e2e_report(
    report: GenerationE2EReport,
    cleanup: PersistenceCleanupResult,
) -> GenerationE2EReport:
    persistence = PersistenceTrace(
        validation_user_id=report.persistence.validation_user_id,
        inserted_ids=report.persistence.inserted_ids,
        inserted_count=cleanup.inserted_count,
        deleted_count=cleanup.deleted_count,
        remaining_rows=cleanup.remaining_rows,
        cleanup_completed=cleanup.cleanup_completed,
        cleanup_sql=cleanup.cleanup_sql,
    )
    behavior_valid = (
        report.failed_cases == 0
        and report.suspicious_novelty_cases == 0
        and all(result.prompt_context_non_empty for result in report.cases)
        and all(result.pinecone_order_preserved for result in report.cases)
        and report.fail_open_validation.fail_open_generation_succeeded
        and report.fail_open_validation.fail_open_failure_logged
        and report.fail_open_validation.fail_closed_error_propagated
        and report.fail_open_validation.fail_closed_gemini_calls == 0
        and report.reranker.construction_attempts == 0
        and cleanup.cleanup_completed
        and cleanup.deleted_count == cleanup.inserted_count
    )

    return report.model_copy(
        update={
            "persistence": persistence,
            "safe_for_production_deployment": (
                behavior_valid and report.code_runner_limitation is None
            ),
        }
    )


@dataclass
class VectorQueryCall:
    filters: dict[str, str | int] | None
    chunks: list[RetrievedChunk]


class TracingVectorRepository:
    def __init__(self, delegate: PineconeRepository) -> None:
        self.delegate = delegate
        self.calls: list[VectorQueryCall] = []

    def query(
        self,
        vector: list[float],
        top_k: int,
        filters: dict[str, str | int] | None = None,
    ) -> list[RetrievedChunk]:
        chunks = self.delegate.query(vector, top_k, filters)
        self.calls.append(VectorQueryCall(filters=filters, chunks=chunks))
        return chunks

    def upsert(
        self,
        vectors: list[tuple[str, list[float], VectorMetadata]],
    ) -> None:
        raise AssertionError(
            f"E2E validation must not upsert {len(vectors)} vectors"
        )


class TracingRetrievalService:
    def __init__(self, delegate: RetrievalService) -> None:
        self.delegate = delegate
        self.calls = 0
        self.results: list[list[RetrievedChunk]] = []

    async def retrieve(
        self,
        query: str,
        topic: str | None = None,
        difficulty: str | None = None,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        self.calls += 1
        chunks = await self.delegate.retrieve(
            query=query,
            topic=topic,
            difficulty=difficulty,
            top_k=top_k,
        )
        self.results.append(chunks)
        return chunks


class TracingContextBuilder:
    def __init__(self) -> None:
        self.delegate = ContextBuilder()
        self.calls: list[list[RetrievedChunk]] = []

    def build(
        self,
        chunks: list[RetrievedChunk],
        max_chunks: int = CONTEXT_TOP_K,
    ) -> str:
        self.calls.append(chunks[:max_chunks])
        return self.delegate.build(chunks, max_chunks=max_chunks)


class TracingPromptBuilder(PromptBuilder):
    def __init__(self) -> None:
        self.contexts: list[str] = []

    def build_exercise_prompt(
        self,
        request: ExerciseRequest,
        context: str = "",
    ) -> str:
        self.contexts.append(context)
        return super().build_exercise_prompt(request, context=context)


class TracingLLMClient:
    def __init__(self, delegate: LLMClient) -> None:
        self.delegate = delegate
        self.calls = 0

    def generate_exercise(self, prompt: str) -> ExerciseResponse:
        self.calls += 1
        return self.delegate.generate_exercise(prompt)


class TracingCodeRunner:
    def __init__(self, delegate: CodeRunnerProtocol) -> None:
        self.delegate = delegate
        self.calls = 0
        self.result = "not_run"
        self.error: str | None = None

    def validate_cpp(self, code: str) -> None:
        self.calls += 1
        self._run(lambda: self.delegate.validate_cpp(code))

    def validate_cpp_with_test_cases(
        self,
        code: str,
        test_cases: list[ExerciseTestCase],
    ) -> None:
        self.calls += 1
        self._run(
            lambda: self.delegate.validate_cpp_with_test_cases(
                code,
                test_cases,
            )
        )

    def _run(self, operation: Callable[[], None]) -> None:
        try:
            operation()
        except Exception as exc:
            self.result = "failed"
            self.error = f"{type(exc).__name__}: {exc}"
            raise
        self.result = "passed"
        self.error = None


class ForbiddenRerankerFactory:
    def __init__(self) -> None:
        self.construction_attempts = 0

    def __call__(self) -> RerankerProtocol:
        self.construction_attempts += 1
        raise AssertionError(
            "Discovery Engine reranker must not be constructed during E2E validation"
        )


class _RagLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


class _CaseRetrievalFactory:
    def __init__(self) -> None:
        self.vector_repository: TracingVectorRepository | None = None
        self.retrieval_service: TracingRetrievalService | None = None

    def __call__(self) -> RetrievalServiceProtocol:
        vector_repository = TracingVectorRepository(PineconeRepository())
        retrieval_service = TracingRetrievalService(
            RetrievalService(
                embedding_client=VertexEmbeddingClient(),
                vector_repository=vector_repository,
            )
        )
        self.vector_repository = vector_repository
        self.retrieval_service = retrieval_service
        return retrieval_service


async def run_e2e_validation(
    cases: list[GenerationCase] | None = None,
    *,
    validation_user_id: str | None = None,
) -> GenerationE2EReport:
    selected_cases = cases or DEFAULT_CASES
    active_validation_user_id = validation_user_id or create_validation_user_id()
    index_snapshot = _load_index_snapshot()
    _validate_preflight(index_snapshot)

    gemini_client = GeminiClient(
        project=settings.gemini_project,
        location=settings.gemini_location,
        model=settings.gemini_model,
        max_output_tokens=settings.gemini_max_output_tokens,
    )
    reranker_factory = ForbiddenRerankerFactory()
    case_results: list[GenerationCaseResult] = []

    for position, case in enumerate(selected_cases):
        if position > 0:
            await asyncio.sleep(CASE_COOLDOWN_SECONDS)
        case_results.append(
            await _run_generation_case(
                case,
                gemini_client=gemini_client,
                reranker_factory=reranker_factory,
                validation_user_id=active_validation_user_id,
            )
        )

    fail_open_result = await _run_fail_open_validation(
        gemini_client=gemini_client,
        reranker_factory=reranker_factory,
        validation_user_id=active_validation_user_id,
    )
    successful_cases = sum(result.generation_success for result in case_results)
    failed_cases = len(case_results) - successful_cases
    fallback_cases = sum(
        result.semantic_fallback_triggered for result in case_results
    )
    suspicious_novelty_cases = sum(
        result.highest_reference_similarity is not None
        and result.highest_reference_similarity.suspicious
        for result in case_results
    )
    code_runner_limitation = _code_runner_limitation()
    inserted_ids = [
        result.persisted_exercise_id
        for result in case_results
        if result.persisted_exercise_id is not None
    ]
    if fail_open_result.fail_open_persisted_exercise_id is not None:
        inserted_ids.append(
            fail_open_result.fail_open_persisted_exercise_id
        )

    return GenerationE2EReport(
        generated_at=datetime.now(UTC),
        index=index_snapshot,
        cases=case_results,
        successful_cases=successful_cases,
        failed_cases=failed_cases,
        fallback_cases=fallback_cases,
        suspicious_novelty_cases=suspicious_novelty_cases,
        fail_open_validation=fail_open_result,
        reranker=RerankerTrace(
            configured_enabled=settings.reranker_enabled,
            construction_attempts=reranker_factory.construction_attempts,
            discovery_engine_used=reranker_factory.construction_attempts > 0,
        ),
        persistence=PersistenceTrace(
            validation_user_id=active_validation_user_id,
            inserted_ids=inserted_ids,
            inserted_count=len(inserted_ids),
            deleted_count=0,
            remaining_rows=len(inserted_ids),
            cleanup_completed=False,
            cleanup_sql=build_validation_cleanup_sql(active_validation_user_id),
        ),
        code_runner_limitation=code_runner_limitation,
        safe_for_production_deployment=False,
    )


async def _run_generation_case(
    case: GenerationCase,
    *,
    gemini_client: GeminiClient,
    reranker_factory: ForbiddenRerankerFactory,
    validation_user_id: str,
) -> GenerationCaseResult:
    started_at = perf_counter()
    retrieval_factory = _CaseRetrievalFactory()
    context_builder = TracingContextBuilder()
    prompt_builder = TracingPromptBuilder()
    llm_client = TracingLLMClient(gemini_client)
    code_runner = TracingCodeRunner(_configured_code_runner())
    provider = RagContextProvider(
        retrieval_service_factory=retrieval_factory,
        reranker_factory=reranker_factory,
        context_builder=context_builder,
        rag_enabled=True,
        reranker_enabled=False,
        rag_fail_open=False,
        context_top_k=CONTEXT_TOP_K,
    )
    exercise: Exercise | None = None
    error: str | None = None

    try:
        async with session_factory() as session:
            service = ExerciseService(
                prompt_builder=prompt_builder,
                llm_client=llm_client,
                validator=ExerciseValidator(CodeValidator(code_runner)),
                repository=ExerciseRepository(session),
                rag_context_provider=provider,
                novelty_validator=ExerciseNoveltyValidator(),
            )
            exercise = await service.generate(
                ExerciseRequest(
                    topic=case.topic,
                    difficulty=case.difficulty,
                ),
                validation_user_id,
            )
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        logger.exception("E2E generation case '%s' failed", case.id)

    retrieval_service = retrieval_factory.retrieval_service
    vector_repository = retrieval_factory.vector_repository
    retrieved_chunks = (
        retrieval_service.results[-1]
        if retrieval_service is not None and retrieval_service.results
        else []
    )
    vector_calls = vector_repository.calls if vector_repository is not None else []
    filtered_chunks = vector_calls[0].chunks if vector_calls else []
    fallback_triggered = (
        len(vector_calls) >= 2
        and vector_calls[0].filters is not None
        and vector_calls[1].filters is None
    )
    context_chunks = context_builder.calls[-1] if context_builder.calls else []
    response = _exercise_to_response(exercise) if exercise is not None else None
    highest_similarity = (
        find_highest_reference_similarity(response, retrieved_chunks)
        if response is not None
        else None
    )

    return GenerationCaseResult(
        case_id=case.id,
        requested_topic=case.topic,
        requested_difficulty=case.difficulty,
        retrieval_service_called=(
            retrieval_service is not None and retrieval_service.calls > 0
        ),
        retrieved_documents=[
            RetrievedDocumentTrace(
                id=chunk.id,
                score=chunk.score,
                topic=chunk.topic,
                source=chunk.source,
                year=chunk.year,
            )
            for chunk in retrieved_chunks
        ],
        initial_filtered_result_count=len(filtered_chunks),
        filtered_retrieval_succeeded=(
            bool(vector_calls)
            and vector_calls[0].filters is not None
            and len(filtered_chunks) >= 8
            and not fallback_triggered
        ),
        semantic_fallback_triggered=fallback_triggered,
        context_chunk_count=len(context_chunks),
        context_chunk_ids=[chunk.id for chunk in context_chunks],
        pinecone_order_preserved=(
            [chunk.id for chunk in context_chunks]
            == [chunk.id for chunk in retrieved_chunks[:CONTEXT_TOP_K]]
        ),
        prompt_context_non_empty=(
            bool(prompt_builder.contexts)
            and all(bool(context) for context in prompt_builder.contexts)
        ),
        generation_attempts=llm_client.calls,
        generation_success=exercise is not None,
        validator_result=("passed" if exercise is not None else "failed"),
        code_execution=_code_execution_trace(code_runner),
        persisted_exercise_id=exercise.id if exercise is not None else None,
        generated_statement=exercise.statement if exercise is not None else None,
        highest_reference_similarity=highest_similarity,
        elapsed_ms=(perf_counter() - started_at) * 1000,
        error=error,
    )


async def _run_fail_open_validation(
    *,
    gemini_client: GeminiClient,
    reranker_factory: ForbiddenRerankerFactory,
    validation_user_id: str,
) -> FailOpenValidationResult:
    def failing_retrieval_factory() -> RetrievalServiceProtocol:
        raise RuntimeError("simulated embedding initialization failure")

    context_builder = TracingContextBuilder()
    prompt_builder = TracingPromptBuilder()
    llm_client = TracingLLMClient(gemini_client)
    code_runner = TracingCodeRunner(_configured_code_runner())
    provider = RagContextProvider(
        retrieval_service_factory=failing_retrieval_factory,
        reranker_factory=reranker_factory,
        context_builder=context_builder,
        rag_enabled=True,
        reranker_enabled=False,
        rag_fail_open=True,
    )
    log_handler = _RagLogHandler()
    rag_logger = logging.getLogger(
        "bac_generator.services.rag_context_provider"
    )
    rag_logger.addHandler(log_handler)
    exercise: Exercise | None = None

    try:
        async with session_factory() as session:
            service = ExerciseService(
                prompt_builder=prompt_builder,
                llm_client=llm_client,
                validator=ExerciseValidator(CodeValidator(code_runner)),
                repository=ExerciseRepository(session),
                rag_context_provider=provider,
                novelty_validator=ExerciseNoveltyValidator(),
            )
            exercise = await service.generate(
                ExerciseRequest(topic="arrays", difficulty=Difficulty.EASY),
                validation_user_id,
            )
    finally:
        rag_logger.removeHandler(log_handler)

    fail_closed_llm = TracingLLMClient(gemini_client)
    fail_closed_provider = RagContextProvider(
        retrieval_service_factory=failing_retrieval_factory,
        reranker_factory=reranker_factory,
        context_builder=TracingContextBuilder(),
        rag_enabled=True,
        reranker_enabled=False,
        rag_fail_open=False,
    )
    fail_closed_error: str | None = None

    try:
        async with session_factory() as session:
            service = ExerciseService(
                prompt_builder=TracingPromptBuilder(),
                llm_client=fail_closed_llm,
                validator=ExerciseValidator(
                    CodeValidator(TracingCodeRunner(_configured_code_runner()))
                ),
                repository=ExerciseRepository(session),
                rag_context_provider=fail_closed_provider,
                novelty_validator=ExerciseNoveltyValidator(),
            )
            await service.generate(
                ExerciseRequest(topic="arrays", difficulty=Difficulty.EASY),
                validation_user_id,
            )
    except RuntimeError as exc:
        fail_closed_error = str(exc)

    return FailOpenValidationResult(
        fail_open_generation_succeeded=exercise is not None,
        fail_open_empty_context_used=(
            bool(prompt_builder.contexts)
            and all(context == "" for context in prompt_builder.contexts)
            and not context_builder.calls
        ),
        fail_open_failure_logged=any(
            "Falling back to generation without retrieval context" in message
            for message in log_handler.messages
        ),
        fail_open_validator_result=("passed" if exercise is not None else "failed"),
        fail_open_code_execution=_code_execution_trace(code_runner),
        fail_open_persisted_exercise_id=(
            exercise.id if exercise is not None else None
        ),
        fail_closed_error_propagated=(
            fail_closed_error == "simulated embedding initialization failure"
        ),
        fail_closed_gemini_calls=fail_closed_llm.calls,
        fail_closed_error=fail_closed_error,
    )


def _exercise_to_response(exercise: Exercise) -> ExerciseResponse:
    return ExerciseResponse(
        topic=exercise.topic,
        difficulty=Difficulty(exercise.difficulty),
        statement=exercise.statement,
        solution=exercise.solution,
        explanation=exercise.explanation,
        test_cases=[
            ExerciseTestCase.model_validate(test_case)
            for test_case in exercise.test_cases
        ],
    )


def _configured_code_runner() -> CodeRunnerProtocol:
    if settings.code_runner_provider == "local":
        return LocalCodeRunner()

    if settings.code_runner_provider == "sandbox":
        return SandboxCodeRunner()

    raise ValueError(
        f"Unsupported code runner provider: {settings.code_runner_provider}"
    )


def _code_execution_trace(runner: TracingCodeRunner) -> CodeExecutionTrace:
    delegate_name = type(runner.delegate).__name__
    return CodeExecutionTrace(
        configured_provider=settings.code_runner_provider,
        runner=delegate_name,
        sandbox_used=isinstance(runner.delegate, SandboxCodeRunner),
        calls=runner.calls,
        result=runner.result,
        error=runner.error,
    )


def _load_index_snapshot() -> IndexSnapshot:
    client = Pinecone(api_key=settings.pinecone_api_key)
    description = client.describe_index(settings.pinecone_index_name)
    stats = client.Index(settings.pinecone_index_name).describe_index_stats()
    namespace = stats.namespaces.get(settings.pinecone_namespace)

    return IndexSnapshot(
        index_name=settings.pinecone_index_name,
        namespace=settings.pinecone_namespace,
        dimension=int(description.dimension or 0),
        metric=str(description.metric),
        namespace_vector_count=(
            int(namespace.vector_count or 0) if namespace is not None else 0
        ),
        total_vector_count=int(stats.total_vector_count or 0),
        namespaces=sorted(stats.namespaces),
    )


def _validate_preflight(snapshot: IndexSnapshot) -> None:
    if settings.reranker_enabled:
        raise RuntimeError("RERANKER_ENABLED must be false for E2E validation")

    expected_namespaces = [settings.pinecone_namespace]
    errors: list[str] = []

    if snapshot.dimension != EXPECTED_DIMENSION:
        errors.append(
            f"dimension={snapshot.dimension}, expected={EXPECTED_DIMENSION}"
        )
    if snapshot.metric != EXPECTED_METRIC:
        errors.append(f"metric={snapshot.metric}, expected={EXPECTED_METRIC}")
    if snapshot.namespace_vector_count != EXPECTED_VECTOR_COUNT:
        errors.append(
            "namespace_vector_count="
            f"{snapshot.namespace_vector_count}, expected={EXPECTED_VECTOR_COUNT}"
        )
    if snapshot.total_vector_count != EXPECTED_VECTOR_COUNT:
        errors.append(
            f"total_vector_count={snapshot.total_vector_count}, "
            f"expected={EXPECTED_VECTOR_COUNT}"
        )
    if snapshot.namespaces != expected_namespaces:
        errors.append(
            f"namespaces={snapshot.namespaces}, expected={expected_namespaces}"
        )

    if errors:
        raise RuntimeError("Pinecone preflight failed: " + "; ".join(errors))


def _code_runner_limitation() -> str | None:
    if settings.code_runner_provider == "sandbox":
        return None

    return (
        "Cloud Run sandbox launcher is unavailable in this local environment; "
        "C++ compilation/runtime was validated with LocalCodeRunner instead."
    )

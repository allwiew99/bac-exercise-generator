from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime
from typing import Any

from bac_generator.evaluation.rag.generation_e2e import (
    CodeExecutionTrace,
    FailOpenValidationResult,
    GenerationE2EReport,
    IndexSnapshot,
    PersistenceCleanupResult,
    PersistenceTrace,
    RerankerTrace,
    build_validation_cleanup_sql,
    cleanup_validation_rows,
    create_validation_user_id,
    finalize_e2e_report,
    validation_cleanup_statement,
)


class FakeCleanupSession:
    def __init__(self) -> None:
        self.scalar_results = [3, 0]
        self.scalar_statements: list[Any] = []
        self.execute_statements: list[Any] = []
        self.committed = False

    async def scalar(self, statement: Any) -> int:
        self.scalar_statements.append(statement)
        return self.scalar_results.pop(0)

    async def execute(self, statement: Any) -> None:
        self.execute_statements.append(statement)

    async def commit(self) -> None:
        self.committed = True


class FakeSessionContext(AbstractAsyncContextManager[FakeCleanupSession]):
    def __init__(self, session: FakeCleanupSession) -> None:
        self.session = session

    async def __aenter__(self) -> FakeCleanupSession:
        return self.session

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        return None


def test_validation_user_id_is_unique_and_unambiguously_non_user() -> None:
    first = create_validation_user_id()
    second = create_validation_user_id()

    assert first.startswith("__rag_e2e_validation__")
    assert second.startswith("__rag_e2e_validation__")
    assert first != second


def test_cleanup_statement_targets_only_the_exact_validation_uid() -> None:
    validation_uid = "__rag_e2e_validation__run-123"
    statement = validation_cleanup_statement(validation_uid)
    compiled = statement.compile()

    assert list(compiled.params.values()) == [validation_uid]
    assert "DELETE FROM exercises WHERE exercises.user_id =" in str(compiled)
    assert build_validation_cleanup_sql(validation_uid) == (
        "DELETE FROM exercises WHERE user_id = "
        "'__rag_e2e_validation__run-123';"
    )


async def test_cleanup_reports_deleted_count_and_zero_remaining_rows() -> None:
    session = FakeCleanupSession()

    result = await cleanup_validation_rows(
        "__rag_e2e_validation__run-123",
        session_factory_override=lambda: FakeSessionContext(session),
    )

    assert result.inserted_count == 3
    assert result.deleted_count == 3
    assert result.remaining_rows == 0
    assert result.cleanup_completed is True
    assert session.committed is True
    assert len(session.execute_statements) == 1


async def test_cleanup_is_not_marked_complete_when_rows_remain() -> None:
    session = FakeCleanupSession()
    session.scalar_results = [3, 1]

    result = await cleanup_validation_rows(
        "__rag_e2e_validation__run-123",
        session_factory_override=lambda: FakeSessionContext(session),
    )

    assert result.deleted_count == 2
    assert result.remaining_rows == 1
    assert result.cleanup_completed is False


def test_finalize_report_requires_complete_exact_uid_cleanup() -> None:
    code_execution = CodeExecutionTrace(
        configured_provider="local",
        runner="LocalCodeRunner",
        sandbox_used=False,
        calls=1,
        result="passed",
        error=None,
    )
    report = GenerationE2EReport(
        generated_at=datetime.now(UTC),
        index=IndexSnapshot(
            index_name="index",
            namespace="namespace",
            dimension=768,
            metric="cosine",
            namespace_vector_count=317,
            total_vector_count=317,
            namespaces=["namespace"],
        ),
        cases=[],
        successful_cases=0,
        failed_cases=0,
        fallback_cases=0,
        suspicious_novelty_cases=0,
        fail_open_validation=FailOpenValidationResult(
            fail_open_generation_succeeded=True,
            fail_open_empty_context_used=True,
            fail_open_failure_logged=True,
            fail_open_validator_result="passed",
            fail_open_code_execution=code_execution,
            fail_open_persisted_exercise_id=42,
            fail_closed_error_propagated=True,
            fail_closed_gemini_calls=0,
            fail_closed_error="expected",
        ),
        reranker=RerankerTrace(
            configured_enabled=False,
            construction_attempts=0,
            discovery_engine_used=False,
        ),
        persistence=PersistenceTrace(
            validation_user_id="__rag_e2e_validation__run-123",
            inserted_ids=[42],
            inserted_count=1,
            deleted_count=0,
            remaining_rows=1,
            cleanup_completed=False,
            cleanup_sql="DELETE ...",
        ),
        code_runner_limitation=None,
        safe_for_production_deployment=False,
    )

    finalized = finalize_e2e_report(
        report,
        PersistenceCleanupResult(
            inserted_count=1,
            deleted_count=1,
            remaining_rows=0,
            cleanup_completed=True,
            cleanup_sql="DELETE exact UID",
        ),
    )

    assert finalized.persistence.cleanup_completed is True
    assert finalized.persistence.remaining_rows == 0
    assert finalized.persistence.cleanup_sql == "DELETE exact UID"
    assert finalized.safe_for_production_deployment is True

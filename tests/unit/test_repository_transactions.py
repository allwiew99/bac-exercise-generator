from unittest.mock import AsyncMock, Mock

import pytest

from bac_generator.repositories.exercise_repository import ExerciseRepository
from bac_generator.schemas.exercise import Difficulty, ExerciseResponse, ExerciseTestCase


def _exercise() -> ExerciseResponse:
    return ExerciseResponse(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
        statement="Enunț.",
        solution="int main() { return 0; }",
        explanation="Explicație.",
        test_cases=[ExerciseTestCase(input="1", expected_output="1")],
    )


@pytest.mark.asyncio
async def test_exercise_create_rolls_back_when_commit_fails() -> None:
    session = Mock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock(side_effect=RuntimeError("database unavailable"))
    session.rollback = AsyncMock()
    repository = ExerciseRepository(session)

    with pytest.raises(RuntimeError, match="database unavailable"):
        await repository.create(_exercise(), "user-1")

    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_exercise_create_does_not_commit_when_refresh_fails() -> None:
    session = Mock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock(side_effect=RuntimeError("refresh failed"))
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    repository = ExerciseRepository(session)

    with pytest.raises(RuntimeError, match="refresh failed"):
        await repository.create(_exercise(), "user-1")

    session.commit.assert_not_awaited()
    session.rollback.assert_awaited_once()

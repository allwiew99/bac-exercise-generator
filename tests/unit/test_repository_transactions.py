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
    session.commit = AsyncMock(side_effect=RuntimeError("database unavailable"))
    session.rollback = AsyncMock()
    repository = ExerciseRepository(session)

    with pytest.raises(RuntimeError, match="database unavailable"):
        await repository.create(_exercise(), "user-1")

    session.rollback.assert_awaited_once()

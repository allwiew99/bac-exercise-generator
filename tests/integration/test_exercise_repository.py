import pytest

from bac_generator.db.session import session_factory
from bac_generator.repositories.exercise_repository import ExerciseRepository
from bac_generator.schemas.exercise import Difficulty, ExerciseResponse

pytestmark = pytest.mark.asyncio(loop_scope="module")


async def test_create_persists_exercise() -> None:
    async with session_factory() as session:
        repository = ExerciseRepository(session)

        exercise_data = ExerciseResponse(
            topic="vectori",
            difficulty=Difficulty.MEDIUM,
            statement="Enunț de test.",
            solution="Cod C++ de test.",
            explanation="Explicație de test.",
        )

        saved_exercise = await repository.create(exercise_data)
        try:
            assert saved_exercise.id is not None
            assert saved_exercise.created_at is not None
            assert saved_exercise.topic == exercise_data.topic
            assert saved_exercise.difficulty == exercise_data.difficulty

        finally:
            await session.delete(saved_exercise)
            await session.commit()


async def test_get_by_id_returns_existing_exercise() -> None:
    async with session_factory() as session:
        repository = ExerciseRepository(session)

        exercise_data = ExerciseResponse(
            topic="vectori",
            difficulty=Difficulty.MEDIUM,
            statement="Enunț de test.",
            solution="Cod C++ de test.",
            explanation="Explicație de test.",
        )

        saved_exercise = await repository.create(exercise_data)

        try:
            found_exercise = await repository.get_by_id(saved_exercise.id)

            assert found_exercise is not None
            assert found_exercise.id == saved_exercise.id
            assert found_exercise.topic == exercise_data.topic
        finally:
            await session.delete(saved_exercise)
            await session.commit()


async def test_get_by_id_returns_none_for_missing_exercise() -> None:
    async with session_factory() as session:
        repository = ExerciseRepository(session)
        non_existent_id = 999999
        found_exercise = await repository.get_by_id(non_existent_id)

        assert found_exercise is None


async def test_list_returns_existing_exercises() -> None:
    async with session_factory() as session:
        repository = ExerciseRepository(session)

        exercise_data_1 = ExerciseResponse(
            topic="vectori",
            difficulty=Difficulty.MEDIUM,
            statement="Enunț de test.",
            solution="Cod C++ de test.",
            explanation="Explicație de test.",
        )

        exercise_data_2 = ExerciseResponse(
            topic="matrici",
            difficulty=Difficulty.HARD,
            statement="Enunț de test 2.",
            solution="Cod C++ de test 2.",
            explanation="Explicație de test 2.",
        )

        saved_exercise_1 = await repository.create(exercise_data_1)
        saved_exercise_2 = await repository.create(exercise_data_2)

        try:
            exercises = await repository.list()
            exercise_ids = [exercise.id for exercise in exercises]

            assert saved_exercise_1.id in exercise_ids
            assert saved_exercise_2.id in exercise_ids
        finally:
            await session.delete(saved_exercise_1)
            await session.delete(saved_exercise_2)
            await session.commit()

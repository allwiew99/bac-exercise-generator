from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bac_generator.db.models import Exercise
from bac_generator.schemas.exercise import ExerciseResponse


class ExerciseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        exercise_data: ExerciseResponse,
    ) -> Exercise:
        exercise = Exercise(
            topic=exercise_data.topic,
            difficulty=exercise_data.difficulty,
            statement=exercise_data.statement,
            solution=exercise_data.solution,
            explanation=exercise_data.explanation,
            test_cases=[test_case.model_dump() for test_case in exercise_data.test_cases],
        )

        self.session.add(exercise)
        await self.session.commit()
        await self.session.refresh(exercise)
        return exercise

    async def get_by_id(self, exercise_id: int) -> Exercise | None:
        result = await self.session.execute(select(Exercise).where(Exercise.id == exercise_id))
        return result.scalar_one_or_none()

    async def list(self) -> list[Exercise]:
        result = await self.session.execute(select(Exercise))
        return list(result.scalars().all())

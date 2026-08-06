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
        )

        self.session.add(exercise)
        await self.session.commit()
        await self.session.refresh(exercise)
        return exercise

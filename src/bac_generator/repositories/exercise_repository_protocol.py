from typing import Protocol

from bac_generator.db.models import Exercise
from bac_generator.schemas.exercise import ExerciseResponse


class ExerciseRepositoryProtocol(Protocol):
    async def create(
        self,
        exercise_data: ExerciseResponse,
        user_id: str,
    ) -> Exercise: ...

    async def get_by_id(
        self,
        exercise_id: int,
        user_id: str,
    ) -> Exercise | None: ...

    async def list(
        self,
        user_id: str,
    ) -> list[Exercise]: ...
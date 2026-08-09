from typing import Protocol

from bac_generator.db.models import Submission
from bac_generator.schemas.submission import (
    SubmissionCreate,
    SubmissionProgress,
)


class SubmissionRepositoryProtocol(Protocol):
    async def create(
        self,
        submission_data: SubmissionCreate,
    ) -> Submission: ...

    async def get_latest_for_exercise(
        self,
        exercise_id: int,
        user_id: str,
    ) -> Submission | None: ...

    async def list_for_exercise(
        self,
        exercise_id: int,
        user_id: str,
    ) -> list[Submission]: ...

    async def get_progress_for_exercise(
        self,
        exercise_id: int,
        user_id: str,
    ) -> SubmissionProgress: ...

    async def get_progress_for_exercises(
        self,
        exercise_ids: list[int],
        user_id: str,
    ) -> dict[int, SubmissionProgress]: ...
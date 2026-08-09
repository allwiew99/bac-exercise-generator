from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bac_generator.db.models import Submission
from bac_generator.schemas.submission import (
    SubmissionCreate,
    SubmissionProgress,
)


class SubmissionRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create(
        self,
        submission_data: SubmissionCreate,
    ) -> Submission:
        submission = Submission(
            exercise_id=submission_data.exercise_id,
            user_id=submission_data.user_id,
            code=submission_data.code,
            score=submission_data.score,
            passed_tests=submission_data.passed_tests,
            total_tests=submission_data.total_tests,
            status=submission_data.status,
            feedback=submission_data.feedback,
        )

        self.session.add(submission)
        await self.session.commit()
        await self.session.refresh(submission)

        return submission

    async def get_latest_for_exercise(
        self,
        exercise_id: int,
        user_id: str,
    ) -> Submission | None:
        result = await self.session.execute(
            select(Submission)
            .where(
                Submission.exercise_id == exercise_id,
                Submission.user_id == user_id,
            )
            .order_by(
                Submission.created_at.desc(),
                Submission.id.desc(),
            )
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def list_for_exercise(
        self,
        exercise_id: int,
        user_id: str,
    ) -> list[Submission]:
        result = await self.session.execute(
            select(Submission)
            .where(
                Submission.exercise_id == exercise_id,
                Submission.user_id == user_id,
            )
            .order_by(
                Submission.created_at.desc(),
                Submission.id.desc(),
            )
        )

        return list(result.scalars().all())
    
    async def get_progress_for_exercise(
        self,
        exercise_id: int,
        user_id: str,
    ) -> SubmissionProgress:
        latest_submission = await self.get_latest_for_exercise(
            exercise_id,
            user_id,
        )

        result = await self.session.execute(
            select(
                func.count(Submission.id),
                func.max(Submission.score),
            ).where(
                Submission.exercise_id == exercise_id,
                Submission.user_id == user_id,
            )
        )

        submission_count, max_score = result.one()

        return SubmissionProgress(
            has_submitted=submission_count > 0,
            latest_score=(
                latest_submission.score
                if latest_submission is not None
                else None
            ),
            submission_count=submission_count,
            completed=max_score == 100,
        )

    async def get_progress_for_exercises(
        self,
        exercise_ids: list[int],
        user_id: str,
    ) -> dict[int, SubmissionProgress]:
        if not exercise_ids:
            return {}

        stats_result = await self.session.execute(
            select(
                Submission.exercise_id,
                func.count(Submission.id),
                func.max(Submission.score),
            )
            .where(
                Submission.exercise_id.in_(exercise_ids),
                Submission.user_id == user_id,
            )
            .group_by(Submission.exercise_id)
        )

        progress_by_exercise: dict[int, SubmissionProgress] = {
            exercise_id: SubmissionProgress(
                has_submitted=False,
                latest_score=None,
                submission_count=0,
                completed=False,
            )
            for exercise_id in exercise_ids
        }

        for exercise_id, submission_count, max_score in stats_result.all():
            progress_by_exercise[exercise_id] = SubmissionProgress(
                has_submitted=submission_count > 0,
                latest_score=None,
                submission_count=submission_count,
                completed=max_score == 100,
            )

        latest_result = await self.session.execute(
            select(Submission)
            .where(
                Submission.exercise_id.in_(exercise_ids),
                Submission.user_id == user_id,
            )
            .order_by(
                Submission.exercise_id,
                Submission.created_at.desc(),
                Submission.id.desc(),
            )
        )

        latest_scores: dict[int, int] = {}

        for submission in latest_result.scalars():
            if submission.exercise_id not in latest_scores:
                latest_scores[submission.exercise_id] = submission.score

        for exercise_id, latest_score in latest_scores.items():
            progress = progress_by_exercise[exercise_id]

            progress_by_exercise[exercise_id] = SubmissionProgress(
                has_submitted=progress.has_submitted,
                latest_score=latest_score,
                submission_count=progress.submission_count,
                completed=progress.completed,
            )

        return progress_by_exercise
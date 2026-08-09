from bac_generator.core.exceptions import SolutionLockedError
from bac_generator.db.models import Submission
from bac_generator.repositories.exercise_repository_protocol import (
    ExerciseRepositoryProtocol,
)
from bac_generator.repositories.submission_repository_protocol import (
    SubmissionRepositoryProtocol,
)
from bac_generator.schemas.exercise import ExerciseTestCase
from bac_generator.schemas.submission import (
    OfficialSolutionRead,
    SubmissionCreate,
    SubmitSolutionRequest,
)
from bac_generator.services.submission_evaluator import SubmissionEvaluator


class SubmissionService:
    def __init__(
        self,
        exercise_repository: ExerciseRepositoryProtocol,
        submission_repository: SubmissionRepositoryProtocol,
        evaluator: SubmissionEvaluator,
    ) -> None:
        self.exercise_repository = exercise_repository
        self.submission_repository = submission_repository
        self.evaluator = evaluator

    async def submit_solution(
        self,
        exercise_id: int,
        user_id: str,
        request: SubmitSolutionRequest,
    ) -> Submission | None:
        exercise = await self.exercise_repository.get_by_id(
            exercise_id,
            user_id,
        )

        if exercise is None:
            return None

        test_cases = [
            ExerciseTestCase.model_validate(test_case)
            for test_case in exercise.test_cases
        ]

        evaluation = self.evaluator.evaluate(
            request.code,
            test_cases,
        )

        submission_data = SubmissionCreate(
            exercise_id=exercise_id,
            user_id=user_id,
            code=request.code,
            score=evaluation.score,
            passed_tests=evaluation.passed_tests,
            total_tests=evaluation.total_tests,
            status=evaluation.status,
            feedback=evaluation.feedback,
        )

        submission = await self.submission_repository.create(
            submission_data
        )

        return submission

    async def get_official_solution(
        self,
        exercise_id: int,
        user_id: str,
    ) -> OfficialSolutionRead | None:
        exercise = await self.exercise_repository.get_by_id(
            exercise_id,
            user_id,
        )

        if exercise is None:
            return None

        submission = (
            await self.submission_repository.get_latest_for_exercise(
                exercise_id,
                user_id,
            )
        )

        if submission is None:
            raise SolutionLockedError(
                "Official solution is available only after submitting a solution."
            )

        return OfficialSolutionRead(
            solution=exercise.solution,
            explanation=exercise.explanation,
        )
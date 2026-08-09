from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from bac_generator.ai.gemini_client import GeminiClient
from bac_generator.ai.llm_client import LLMClient
from bac_generator.ai.ollama_client import OllamaClient
from bac_generator.ai.prompt_builder import PromptBuilder
from bac_generator.api.dependencies.auth import (
    CurrentUser,
    get_current_user,
)
from bac_generator.core.config import settings
from bac_generator.core.exceptions import RateLimitExceededError
from bac_generator.db.models import Exercise
from bac_generator.db.session import get_db_session
from bac_generator.repositories.exercise_repository import (
    ExerciseRepository,
)
from bac_generator.repositories.submission_repository import (
    SubmissionRepository,
)
from bac_generator.schemas.exercise import (
    Difficulty,
    ExerciseRequest,
    ExerciseSafeRead,
    ExerciseSampleTestCase,
    ExerciseTestCase,
)
from bac_generator.schemas.submission import (
    OfficialSolutionRead,
    SubmissionProgress,
    SubmissionRead,
    SubmitSolutionRequest,
)
from bac_generator.services.code_validator import CodeValidator
from bac_generator.services.exercise_service import ExerciseService
from bac_generator.services.exercise_validator import ExerciseValidator
from bac_generator.services.local_code_runner import LocalCodeRunner
from bac_generator.services.rate_limiter import (
    InMemoryRateLimiter,
    RateLimiterProtocol,
)
from bac_generator.services.sandbox_code_runner import SandboxCodeRunner
from bac_generator.services.submission_evaluator import (
    SubmissionEvaluator,
)
from bac_generator.services.submission_service import SubmissionService

router = APIRouter(
    prefix="/exercises",
    tags=["exercises"],
)


rate_limiter = InMemoryRateLimiter()


def to_safe_exercise_read(
    exercise: Exercise,
    progress: SubmissionProgress | None = None,
) -> ExerciseSafeRead:
    sample_test_cases: list[ExerciseSampleTestCase] = []

    for raw_test_case in exercise.test_cases:
        test_case = ExerciseTestCase.model_validate(
            raw_test_case
        )

        if not test_case.is_hidden:
            sample_test_cases.append(
                ExerciseSampleTestCase(
                    input=test_case.input,
                    expected_output=test_case.expected_output,
                )
            )

    return ExerciseSafeRead(
        id=exercise.id,
        topic=exercise.topic,
        difficulty=Difficulty(exercise.difficulty),
        statement=exercise.statement,
        created_at=exercise.created_at,
        sample_test_cases=sample_test_cases,
        has_submitted=(
            progress.has_submitted
            if progress is not None
            else False
        ),
        latest_score=(
            progress.latest_score
            if progress is not None
            else None
        ),
        submission_count=(
            progress.submission_count
            if progress is not None
            else 0
        ),
        completed=(
            progress.completed
            if progress is not None
            else False
        ),
    )


def get_prompt_builder() -> PromptBuilder:
    return PromptBuilder()


def get_llm_client() -> LLMClient:
    if settings.llm_provider == "ollama":
        return OllamaClient(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )

    if settings.llm_provider == "gemini":
        return GeminiClient(
            project=settings.gemini_project,
            location=settings.gemini_location,
            model=settings.gemini_model,
        )

    raise ValueError(
        f"Unsupported LLM provider: {settings.llm_provider}"
    )


def get_code_validator() -> CodeValidator:
    if settings.code_runner_provider == "local":
        return CodeValidator(
            runner=LocalCodeRunner(),
        )

    if settings.code_runner_provider == "sandbox":
        return CodeValidator(
            runner=SandboxCodeRunner(),
        )

    raise ValueError(
        "Unsupported code runner provider: "
        f"{settings.code_runner_provider}"
    )


def get_exercise_validator(
    code_validator: Annotated[
        CodeValidator,
        Depends(get_code_validator),
    ],
) -> ExerciseValidator:
    return ExerciseValidator(code_validator)


def get_exercise_repository(
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> ExerciseRepository:
    return ExerciseRepository(session)


def get_submission_repository(
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> SubmissionRepository:
    return SubmissionRepository(session)


def get_submission_evaluator() -> SubmissionEvaluator:
    return SubmissionEvaluator()


def get_rate_limiter() -> RateLimiterProtocol:
    return rate_limiter


async def enforce_generate_rate_limit(
    current_user: Annotated[
        CurrentUser,
        Depends(get_current_user),
    ],
    limiter: Annotated[
        RateLimiterProtocol,
        Depends(get_rate_limiter),
    ],
) -> None:
    allowed = await limiter.check(
        key=f"generate:{current_user.uid}",
        limit=10,
        window_seconds=60,
    )

    if not allowed:
        raise RateLimitExceededError(
            "Too many exercise generation requests. "
            "Please try again shortly."
        )


async def enforce_submission_rate_limit(
    current_user: Annotated[
        CurrentUser,
        Depends(get_current_user),
    ],
    limiter: Annotated[
        RateLimiterProtocol,
        Depends(get_rate_limiter),
    ],
) -> None:
    allowed = await limiter.check(
        key=f"submission:{current_user.uid}",
        limit=30,
        window_seconds=60,
    )

    if not allowed:
        raise RateLimitExceededError(
            "Too many submission requests. "
            "Please try again shortly."
        )


def get_exercise_service(
    prompt_builder: Annotated[
        PromptBuilder,
        Depends(get_prompt_builder),
    ],
    llm_client: Annotated[
        LLMClient,
        Depends(get_llm_client),
    ],
    validator: Annotated[
        ExerciseValidator,
        Depends(get_exercise_validator),
    ],
    repository: Annotated[
        ExerciseRepository,
        Depends(get_exercise_repository),
    ],
) -> ExerciseService:
    return ExerciseService(
        prompt_builder=prompt_builder,
        llm_client=llm_client,
        validator=validator,
        repository=repository,
    )


def get_submission_service(
    exercise_repository: Annotated[
        ExerciseRepository,
        Depends(get_exercise_repository),
    ],
    submission_repository: Annotated[
        SubmissionRepository,
        Depends(get_submission_repository),
    ],
    evaluator: Annotated[
        SubmissionEvaluator,
        Depends(get_submission_evaluator),
    ],
) -> SubmissionService:
    return SubmissionService(
        exercise_repository=exercise_repository,
        submission_repository=submission_repository,
        evaluator=evaluator,
    )


@router.post(
    "/generate",
    response_model=ExerciseSafeRead,
    dependencies=[
        Depends(enforce_generate_rate_limit),
    ],
)
async def generate_exercise(
    request: ExerciseRequest,
    current_user: Annotated[
        CurrentUser,
        Depends(get_current_user),
    ],
    service: Annotated[
        ExerciseService,
        Depends(get_exercise_service),
    ],
) -> ExerciseSafeRead:
    exercise = await service.generate(
        request,
        current_user.uid,
    )

    return to_safe_exercise_read(exercise)


@router.get(
    "/",
    response_model=list[ExerciseSafeRead],
)
async def list_exercises(
    current_user: Annotated[
        CurrentUser,
        Depends(get_current_user),
    ],
    service: Annotated[
        ExerciseService,
        Depends(get_exercise_service),
    ],
    submission_repository: Annotated[
        SubmissionRepository,
        Depends(get_submission_repository),
    ],
) -> list[ExerciseSafeRead]:
    exercises = await service.list_exercises(
        current_user.uid,
    )

    exercise_ids = [
        exercise.id
        for exercise in exercises
    ]

    progress_by_exercise = (
        await submission_repository.get_progress_for_exercises(
            exercise_ids,
            current_user.uid,
        )
    )

    return [
        to_safe_exercise_read(
            exercise,
            progress_by_exercise.get(exercise.id),
        )
        for exercise in exercises
    ]


@router.get(
    "/{exercise_id}",
    response_model=ExerciseSafeRead,
)
async def get_exercise_by_id(
    exercise_id: int,
    current_user: Annotated[
        CurrentUser,
        Depends(get_current_user),
    ],
    service: Annotated[
        ExerciseService,
        Depends(get_exercise_service),
    ],
    submission_repository: Annotated[
        SubmissionRepository,
        Depends(get_submission_repository),
    ],
) -> ExerciseSafeRead:
    exercise = await service.get_exercise_by_id(
        exercise_id,
        current_user.uid,
    )

    if exercise is None:
        raise HTTPException(
            status_code=404,
            detail="Exercise not found.",
        )

    progress = (
        await submission_repository.get_progress_for_exercise(
            exercise_id,
            current_user.uid,
        )
    )

    return to_safe_exercise_read(
        exercise,
        progress,
    )


@router.post(
    "/{exercise_id}/submissions",
    response_model=SubmissionRead,
    dependencies=[
        Depends(enforce_submission_rate_limit),
    ],
)
async def submit_solution(
    exercise_id: int,
    request: SubmitSolutionRequest,
    current_user: Annotated[
        CurrentUser,
        Depends(get_current_user),
    ],
    service: Annotated[
        SubmissionService,
        Depends(get_submission_service),
    ],
) -> SubmissionRead:
    submission = await service.submit_solution(
        exercise_id=exercise_id,
        user_id=current_user.uid,
        request=request,
    )

    if submission is None:
        raise HTTPException(
            status_code=404,
            detail="Exercise not found.",
        )

    return SubmissionRead.model_validate(
        submission
    )


@router.get(
    "/{exercise_id}/solution",
    response_model=OfficialSolutionRead,
)
async def get_official_solution(
    exercise_id: int,
    current_user: Annotated[
        CurrentUser,
        Depends(get_current_user),
    ],
    service: Annotated[
        SubmissionService,
        Depends(get_submission_service),
    ],
) -> OfficialSolutionRead:
    solution = await service.get_official_solution(
        exercise_id=exercise_id,
        user_id=current_user.uid,
    )

    if solution is None:
        raise HTTPException(
            status_code=404,
            detail="Exercise not found.",
        )

    return solution
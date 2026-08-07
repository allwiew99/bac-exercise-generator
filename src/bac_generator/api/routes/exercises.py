from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from bac_generator.ai.gemini_client import GeminiClient
from bac_generator.ai.llm_client import LLMClient
from bac_generator.ai.ollama_client import OllamaClient
from bac_generator.ai.prompt_builder import PromptBuilder
from bac_generator.core.config import settings
from bac_generator.db.session import get_db_session
from bac_generator.repositories.exercise_repository import ExerciseRepository
from bac_generator.schemas.exercise import (
    ExerciseRead,
    ExerciseRequest,
    ExerciseResponse,
)
from bac_generator.services.code_validator import CodeValidator
from bac_generator.services.exercise_service import ExerciseService
from bac_generator.services.exercise_validator import ExerciseValidator

router = APIRouter(
    prefix="/exercises",
    tags=["exercises"],
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
    return CodeValidator()


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


@router.post(
    "/generate",
    response_model=ExerciseResponse,
)
async def generate_exercise(
    request: ExerciseRequest,
    service: Annotated[
        ExerciseService,
        Depends(get_exercise_service),
    ],
) -> ExerciseResponse:
    return await service.generate(request)


@router.get(
    "/",
    response_model=list[ExerciseRead],
)
async def list_exercises(
    service: Annotated[
        ExerciseService,
        Depends(get_exercise_service),
    ],
) -> list[ExerciseRead]:
    exercises = await service.list_exercises()

    return [ExerciseRead.model_validate(exercise) for exercise in exercises]


@router.get(
    "/{exercise_id}",
    response_model=ExerciseRead,
)
async def get_exercise_by_id(
    exercise_id: int,
    service: Annotated[
        ExerciseService,
        Depends(get_exercise_service),
    ],
) -> ExerciseRead:
    exercise = await service.get_exercise_by_id(exercise_id)

    if exercise is None:
        raise HTTPException(
            status_code=404,
            detail="Exercise not found.",
        )

    return ExerciseRead.model_validate(exercise)

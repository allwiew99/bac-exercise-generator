from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from bac_generator.ai.ollama_client import OllamaClient
from bac_generator.ai.prompt_builder import PromptBuilder
from bac_generator.core.config import settings
from bac_generator.db.session import get_db_session
from bac_generator.repositories.exercise_repository import ExerciseRepository
from bac_generator.schemas.exercise import ExerciseRequest, ExerciseResponse
from bac_generator.services.code_validator import CodeValidator
from bac_generator.services.exercise_service import ExerciseService
from bac_generator.services.exercise_validator import ExerciseValidator

router = APIRouter(
    prefix="/exercises",
    tags=["exercises"],
)


def get_prompt_builder() -> PromptBuilder:
    return PromptBuilder()


def get_ollama_client() -> OllamaClient:
    return OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
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
    ollama_client: Annotated[
        OllamaClient,
        Depends(get_ollama_client),
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
        llm_client=ollama_client,
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

from typing import Annotated

from fastapi import APIRouter, Depends

from bac_generator.ai.ollama_client import OllamaClient
from bac_generator.ai.prompt_builder import PromptBuilder
from bac_generator.core.config import settings
from bac_generator.schemas.exercise import ExerciseRequest, ExerciseResponse
from bac_generator.services.exercise_service import ExerciseService

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

def get_exercise_service(
    prompt_builder: Annotated[
        PromptBuilder,
        Depends(get_prompt_builder),
    ],
    ollama_client: Annotated[
        OllamaClient,
        Depends(get_ollama_client),
    ],
) -> ExerciseService:
    return ExerciseService(
        prompt_builder=prompt_builder,
        llm_client=ollama_client,
    )


@router.post(
    "/generate",
    response_model=ExerciseResponse,
)
def generate_exercise(
    request: ExerciseRequest,
    service: Annotated[
        ExerciseService,
        Depends(get_exercise_service),
    ],
) -> ExerciseResponse:
    return service.generate(request)
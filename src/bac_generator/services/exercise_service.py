import logging

from bac_generator.ai.llm_client import LLMClient
from bac_generator.ai.prompt_builder import PromptBuilder
from bac_generator.repositories.exercise_repository_protocol import (
    ExerciseRepositoryProtocol,
)
from bac_generator.schemas.exercise import ExerciseRequest, ExerciseResponse
from bac_generator.services.exercise_validator import ExerciseValidator

logger = logging.getLogger(__name__)


class ExerciseService:
    def __init__(
        self,
        prompt_builder: PromptBuilder,
        llm_client: LLMClient,
        validator: ExerciseValidator,
        repository: ExerciseRepositoryProtocol,
    ) -> None:
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client
        self.validator = validator
        self.repository = repository

    async def generate(self, request: ExerciseRequest) -> ExerciseResponse:
        logger.info(
            "Generating exercise for topic '%s' with difficulty '%s'.",
            request.topic,
            request.difficulty,
        )
        prompt = self.prompt_builder.build_exercise_prompt(request)
        exercise = self.llm_client.generate_exercise(prompt)

        self.validator.validate(request, exercise)
        await self.repository.create(exercise)
        logger.info("Exercise generated successfully")
        return exercise

import logging

from bac_generator.ai.llm_client import LLMClient
from bac_generator.ai.prompt_builder import PromptBuilder
from bac_generator.core.config import settings
from bac_generator.core.exceptions import (
    ExerciseValidationError,
    LLMResponseError,
)
from bac_generator.db.models.exercise import Exercise
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

    async def generate(
        self,
        request: ExerciseRequest,
    ) -> ExerciseResponse:
        logger.info(
            "Generating exercise for topic '%s' with difficulty '%s'.",
            request.topic,
            request.difficulty,
        )

        prompt = self.prompt_builder.build_exercise_prompt(request)

        for attempt in range(settings.llm_max_attempts):
            attempt_number = attempt + 1

            try:
                exercise = self.llm_client.generate_exercise(prompt)
                self.validator.validate(request, exercise)

            except (ExerciseValidationError, LLMResponseError) as exc:
                is_last_attempt = attempt_number == settings.llm_max_attempts

                if is_last_attempt:
                    raise

                logger.warning(
                    "Exercise generation attempt %d of %d failed: %s",
                    attempt_number,
                    settings.llm_max_attempts,
                    exc,
                )

                prompt = self.prompt_builder.build_repair_prompt(
                    request,
                    str(exc),
                )

                continue

            await self.repository.create(exercise)

            logger.info(
                "Exercise generated successfully on attempt %d.",
                attempt_number,
            )

            return exercise

        raise RuntimeError(
            "Exercise generation loop ended unexpectedly."
        )

    async def list_exercises(self) -> list[Exercise]:
        logger.info("Listing all exercises.")

        exercises = await self.repository.list()

        logger.info(
            "Retrieved %d exercises.",
            len(exercises),
        )

        return exercises

    async def get_exercise_by_id(
        self,
        exercise_id: int,
    ) -> Exercise | None:
        logger.info(
            "Retrieving exercise with id %d.",
            exercise_id,
        )

        exercise = await self.repository.get_by_id(exercise_id)

        return exercise
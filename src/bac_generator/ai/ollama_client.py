import logging
import time

from ollama import Client

from bac_generator.schemas.exercise import ExerciseResponse

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(
        self,
        base_url: str,
        model: str,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self.client = Client(host=base_url)

    def generate_exercise(self, prompt: str) -> ExerciseResponse:
        schema = ExerciseResponse.model_json_schema()

        logger.info(
            "Calling Ollama model '%s'.",
            self.model,
        )

        start_time = time.perf_counter()

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            format=schema,
            think=False,
            options={
                "temperature": 0,
            },
        )

        elapsed_time = time.perf_counter() - start_time

        logger.info(
            "Ollama model '%s' responded in %.2f seconds.",
            self.model,
            elapsed_time,
        )

        content = response.message.content

        if content is None or not content.strip():
            logger.warning(
                "Ollama model '%s' returned empty content.",
                self.model,
            )
            raise ValueError("Ollama returned an empty response.")

        return ExerciseResponse.model_validate_json(content)
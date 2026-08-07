from google import genai
from google.genai import types

from bac_generator.core.exceptions import LLMResponseError
from bac_generator.schemas.exercise import ExerciseResponse


class GeminiClient:
    def __init__(
        self,
        project: str,
        location: str,
        model: str,
    ) -> None:
        self.model = model

        self.client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
        )

    def generate_exercise(
        self,
        prompt: str,
    ) -> ExerciseResponse:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExerciseResponse,
                temperature=0,
            ),
        )

        content = response.text

        if content is None or not content.strip():
            raise LLMResponseError(
                "Gemini returned an empty response."
            )

        try:
            return ExerciseResponse.model_validate_json(content)
        except ValueError as exc:
            raise LLMResponseError(
                f"Gemini returned an invalid response: {exc}"
            ) from exc
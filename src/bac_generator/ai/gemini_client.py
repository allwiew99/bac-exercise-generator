from google import genai
from google.genai import errors, types

from bac_generator.core.exceptions import LLMResponseError
from bac_generator.schemas.exercise import ExerciseResponse


class GeminiClient:
    def __init__(
        self,
        project: str,
        location: str,
        model: str,
        max_output_tokens: int,
    ) -> None:
        if max_output_tokens <= 0:
            raise ValueError(
                "max_output_tokens must be greater than zero."
            )

        self.model = model
        self.max_output_tokens = max_output_tokens

        self.client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
        )

    def generate_exercise(
        self,
        prompt: str,
    ) -> ExerciseResponse:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=ExerciseResponse.model_json_schema(),
                    temperature=0,
                    max_output_tokens=self.max_output_tokens,
                    thinking_config=types.ThinkingConfig(thinking_budget=4096),
                    system_instruction=(
                        "Generate exactly one compact Romanian Bac Informatics "
                        "exercise as schema-valid JSON. Respect every field-size "
                        "bound; never repeat text, enumerate long data, or emit "
                        "manual execution traces. Verify every expected output "
                        "against the supplied C++17 program. The program must use "
                        "standard input and standard output only and contain main()."
                    ),
                ),
            )
        except errors.APIError as exc:
            raise LLMResponseError(
                f"Gemini request failed with API status {exc.code}."
            ) from exc

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

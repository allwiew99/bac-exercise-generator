from ollama import Client

from bac_generator.schemas.exercise import ExerciseResponse


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
        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            format=ExerciseResponse.model_json_schema(),
            options={
                "temperature": 0,
            },
        )

        content = response.message.content

        if content is None:
            raise ValueError("Ollama returned an empty response.")

        return ExerciseResponse.model_validate_json(content)
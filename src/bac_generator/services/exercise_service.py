from bac_generator.ai.llm_client import LLMClient
from bac_generator.ai.prompt_builder import PromptBuilder
from bac_generator.schemas.exercise import ExerciseRequest, ExerciseResponse


class ExerciseService:
    def __init__(
        self,
        prompt_builder: PromptBuilder,
        llm_client: LLMClient,
    ) -> None:
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client

    def generate(self, request: ExerciseRequest) -> ExerciseResponse:
        prompt = self.prompt_builder.build_exercise_prompt(request)
        return self.llm_client.generate_exercise(prompt)
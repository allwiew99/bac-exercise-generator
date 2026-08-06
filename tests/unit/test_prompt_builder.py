from bac_generator.ai.prompt_builder import PromptBuilder
from bac_generator.schemas.exercise import Difficulty, ExerciseRequest


def test_build_exercise_prompt_contains_request_data() -> None:
    builder = PromptBuilder()
    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    prompt = builder.build_exercise_prompt(request)

    assert isinstance(prompt, str)
    assert "vectori" in prompt
    assert "medium" in prompt
    assert "Task:" in prompt
    assert "Requirements:" in prompt
    assert "Output:" in prompt
    assert "statement" in prompt
    assert "solution" in prompt
    assert "explanation" in prompt

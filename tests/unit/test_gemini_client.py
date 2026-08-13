from unittest.mock import Mock, patch

import pytest
from google.genai import errors

from bac_generator.ai.gemini_client import GeminiClient
from bac_generator.core.exceptions import LLMResponseError
from bac_generator.schemas.exercise import Difficulty, ExerciseResponse

VALID_RESPONSE = """
{
  "topic": "arrays",
  "difficulty": "medium",
  "statement": "Enunț.",
  "solution": "int main() { return 0; }",
  "explanation": "Explicație.",
  "test_cases": [
    {"input": "1", "expected_output": "1", "is_hidden": false}
  ]
}
"""


@patch("bac_generator.ai.gemini_client.genai.Client")
def test_gemini_client_forwards_bounded_output_tokens(
    client_factory: Mock,
) -> None:
    response = Mock(text=VALID_RESPONSE)
    client_factory.return_value.models.generate_content.return_value = response
    client = GeminiClient(
        project="project-id",
        location="us-central1",
        model="gemini-2.5-flash",
        max_output_tokens=8192,
    )

    result = client.generate_exercise("prompt")

    request = client_factory.return_value.models.generate_content.call_args
    assert request.kwargs["config"].max_output_tokens == 8192
    assert request.kwargs["config"].thinking_config.thinking_budget == 4096
    assert "compact" in request.kwargs["config"].system_instruction
    assert "standard input" in request.kwargs["config"].system_instruction
    response_schema = request.kwargs["config"].response_json_schema
    assert "1,800" in response_schema["properties"]["statement"]["description"]
    assert request.kwargs["config"].response_schema is None
    assert result.difficulty is Difficulty.MEDIUM


def test_gemini_client_rejects_non_positive_output_limit() -> None:
    with pytest.raises(
        ValueError,
        match="max_output_tokens must be greater than zero",
    ):
        GeminiClient(
            project="project-id",
            location="us-central1",
            model="gemini-2.5-flash",
            max_output_tokens=0,
        )


def test_generation_schema_exposes_bac_sized_field_bounds() -> None:
    schema = ExerciseResponse.model_json_schema()

    assert "1,800" in schema["properties"]["statement"]["description"]
    assert "5,000" in schema["properties"]["solution"]["description"]
    assert "1,800" in schema["properties"]["explanation"]["description"]
    test_case_schema = schema["$defs"]["ExerciseTestCase"]["properties"]
    assert "500" in test_case_schema["input"]["description"]
    assert "500" in test_case_schema["expected_output"]["description"]


@patch("bac_generator.ai.gemini_client.genai.Client")
def test_gemini_api_failure_enters_existing_generation_retry_contract(
    client_factory: Mock,
) -> None:
    client_factory.return_value.models.generate_content.side_effect = (
        errors.ClientError(
            429,
            {"error": {"status": "RESOURCE_EXHAUSTED"}},
        )
    )
    client = GeminiClient(
        project="project-id",
        location="us-central1",
        model="gemini-2.5-flash",
        max_output_tokens=8192,
    )

    with pytest.raises(LLMResponseError, match="Gemini request failed.*429"):
        client.generate_exercise("prompt")

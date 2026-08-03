from unittest.mock import Mock

import pytest

from bac_generator.ai.ollama_client import OllamaClient
from bac_generator.schemas.exercise import Difficulty, ExerciseResponse


def test_generate_exercise_returns_validated_response() -> None:
    ollama_client = OllamaClient(
        base_url="http://localhost:11434",
        model="test-model",
    )

    mock_response = Mock()
    mock_response.message.content = """
    {
        "topic": "vectori",
        "difficulty": "medium",
        "statement": "Enunț de test.",
        "solution": "Soluție de test.",
        "explanation": "Explicație de test."
    }
    """

    ollama_client.client = Mock()
    ollama_client.client.chat.return_value = mock_response

    result = ollama_client.generate_exercise("prompt de test")

    assert isinstance(result, ExerciseResponse)
    assert result.topic == "vectori"
    assert result.difficulty is Difficulty.MEDIUM
    assert result.statement == "Enunț de test."
    assert result.solution == "Soluție de test."
    assert result.explanation == "Explicație de test."

def test_generate_exercise_rejects_empty_content() -> None:
    ollama_client = OllamaClient(
        base_url="http://localhost:11434",
        model="test-model",
    )

    mock_response = Mock()
    mock_response.message.content = None

    ollama_client.client = Mock()
    ollama_client.client.chat.return_value = mock_response

    with pytest.raises(
        ValueError,
        match="Ollama returned an empty response.",
    ):
        ollama_client.generate_exercise("prompt de test")
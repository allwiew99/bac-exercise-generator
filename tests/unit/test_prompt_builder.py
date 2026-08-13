from bac_generator.ai.prompt_builder import PromptBuilder
from bac_generator.schemas.exercise import (
    Difficulty,
    ExerciseRequest,
    ExerciseResponse,
    ExerciseTestCase,
)


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


def test_prompt_requires_complete_stdin_stdout_cpp17_program() -> None:
    prompt = PromptBuilder().build_exercise_prompt(
        ExerciseRequest(topic="arrays", difficulty=Difficulty.MEDIUM)
    )

    assert "complete C++17 program" in prompt
    assert "int main()" in prompt
    assert "standard input (stdin)" in prompt
    assert "standard output (stdout)" in prompt
    assert "8,192 output tokens" in prompt
    assert "statement: at most 1,800 characters" in prompt
    assert "solution: at most 5,000 characters" in prompt
    assert "explanation: at most 1,800 characters" in prompt
    assert "input or expected_output: at most 500 characters" in prompt
    assert "Do not include manual execution traces" in prompt


def test_file_topic_prompt_forbids_named_file_io() -> None:
    prompt = PromptBuilder().build_exercise_prompt(
        ExerciseRequest(topic="files", difficulty=Difficulty.HARD)
    )

    assert "conceptual file contents" in prompt
    assert "ifstream" in prompt
    assert "ofstream" in prompt
    assert "freopen" in prompt
    assert "named files" in prompt


def test_subprogram_prompt_requires_main_harness() -> None:
    prompt = PromptBuilder().build_exercise_prompt(
        ExerciseRequest(topic="subprograms", difficulty=Difficulty.HARD)
    )

    assert "student-facing statement" in prompt
    assert "main() harness" in prompt
    assert "invokes the requested subprogram" in prompt


def test_repair_prompt_preserves_executable_contract() -> None:
    previous_response = ExerciseResponse(
        topic="files",
        difficulty=Difficulty.HARD,
        statement="Enunț compact.",
        solution="int main() { return 0; }",
        explanation="Explicație.",
        test_cases=[
            ExerciseTestCase(
                input="1\n",
                expected_output="2\n",
                is_hidden=False,
            )
        ],
    )
    prompt = PromptBuilder().build_repair_prompt(
        ExerciseRequest(topic="files", difficulty=Difficulty.HARD),
        "The previous program used ifstream.",
        previous_response=previous_response,
    )

    assert "complete C++17 program" in prompt
    assert "standard input (stdin)" in prompt
    assert "ifstream" in prompt
    assert "The previous program used ifstream." in prompt
    assert '"statement":"Enunț compact."' in prompt
    assert "Repair this exact candidate" in prompt


def test_output_mismatch_repair_changes_only_reported_expected_output() -> None:
    previous_response = ExerciseResponse(
        topic="matrices",
        difficulty=Difficulty.MEDIUM,
        statement="Enunț.",
        solution="int main() { return 0; }",
        explanation="Explicație.",
        test_cases=[
            ExerciseTestCase(
                input="1\n",
                expected_output="10\n",
                is_hidden=False,
            )
        ],
    )

    prompt = PromptBuilder().build_repair_prompt(
        ExerciseRequest(topic="matrices", difficulty=Difficulty.MEDIUM),
        "Program output does not match expected output. "
        "Input: '1'. Expected: '10'. Actual: '12'.",
        previous_response=previous_response,
    )

    assert "change only the\nexpected_output" in prompt
    assert "Do not alter the statement, solution, explanation" in prompt
    assert "use the reported Actual value" in prompt
    assert "matching Input" in prompt

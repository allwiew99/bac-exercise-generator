import pytest

from bac_generator.core.exceptions import ExerciseValidationError
from bac_generator.schemas.exercise import (
    Difficulty,
    ExerciseRequest,
    ExerciseResponse,
    ExerciseTestCase,
)
from bac_generator.services.exercise_validator import ExerciseValidator

VALID_CPP_SOLUTION = """
#include <iostream>
int main() {
    int value;
    std::cin >> value;
    std::cout << value;
    return 0;
}
"""


class FakeCodeValidator:
    def __init__(self) -> None:
        self.test_case_validation_calls = 0

    def validate_cpp(self, code: str) -> None:
        pass

    def validate_cpp_with_test_cases(
        self,
        code: str,
        test_cases: list[ExerciseTestCase],
    ) -> None:
        self.test_case_validation_calls += 1


def build_valid_test_cases() -> list[ExerciseTestCase]:
    return [
        ExerciseTestCase(
            input="3\n1 2 4",
            expected_output="6",
            is_hidden=False,
        ),
        ExerciseTestCase(
            input="2\n5 5",
            expected_output="10",
            is_hidden=True,
        ),
        ExerciseTestCase(
            input="1\n7",
            expected_output="7",
            is_hidden=True,
        ),
        ExerciseTestCase(
            input="4\n1 1 1 1",
            expected_output="4",
            is_hidden=True,
        ),
    ]


def test_validate_accepts_valid_exercise() -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    exercise = ExerciseResponse(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
        statement="Enunț valid.",
        solution=VALID_CPP_SOLUTION,
        explanation="Explicație validă.",
        test_cases=build_valid_test_cases(),
    )

    validator.validate(request, exercise)


def test_validate_rejects_mismatched_topic() -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    exercise = ExerciseResponse(
        topic="matrici",
        difficulty=Difficulty.MEDIUM,
        statement="Enunț valid.",
        solution=VALID_CPP_SOLUTION,
        explanation="Explicație validă.",
        test_cases=build_valid_test_cases(),
    )

    with pytest.raises(
        ExerciseValidationError,
        match="does not match requested topic",
    ):
        validator.validate(request, exercise)


def test_validate_rejects_mismatched_difficulty() -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    exercise = ExerciseResponse(
        topic="vectori",
        difficulty=Difficulty.HARD,
        statement="Enunț valid.",
        solution=VALID_CPP_SOLUTION,
        explanation="Explicație validă.",
        test_cases=build_valid_test_cases(),
    )

    with pytest.raises(
        ExerciseValidationError,
        match="does not match requested difficulty",
    ):
        validator.validate(request, exercise)


def test_validate_rejects_empty_statement() -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    exercise = ExerciseResponse(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
        statement="",
        solution=VALID_CPP_SOLUTION,
        explanation="Explicație validă.",
        test_cases=build_valid_test_cases(),
    )

    with pytest.raises(
        ExerciseValidationError,
        match="The generated 'statement' field is empty",
    ):
        validator.validate(request, exercise)


def test_validate_rejects_too_few_test_cases() -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    exercise = ExerciseResponse(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
        statement="Enunț valid.",
        solution=VALID_CPP_SOLUTION,
        explanation="Explicație validă.",
        test_cases=[
            ExerciseTestCase(
                input="1",
                expected_output="1",
                is_hidden=False,
            ),
            ExerciseTestCase(
                input="2",
                expected_output="2",
                is_hidden=True,
            ),
            ExerciseTestCase(
                input="3",
                expected_output="3",
                is_hidden=True,
            ),
        ],
    )

    with pytest.raises(
        ExerciseValidationError,
        match="between 4 and 6 test cases",
    ):
        validator.validate(request, exercise)


def test_validate_rejects_too_many_test_cases() -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    exercise = ExerciseResponse(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
        statement="Enunț valid.",
        solution=VALID_CPP_SOLUTION,
        explanation="Explicație validă.",
        test_cases=[
            ExerciseTestCase(
                input=str(index),
                expected_output=str(index),
                is_hidden=index != 1,
            )
            for index in range(1, 8)
        ],
    )

    with pytest.raises(
        ExerciseValidationError,
        match="between 4 and 6 test cases",
    ):
        validator.validate(request, exercise)


def test_validate_rejects_no_public_test_cases() -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    exercise = ExerciseResponse(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
        statement="Enunț valid.",
        solution=VALID_CPP_SOLUTION,
        explanation="Explicație validă.",
        test_cases=[
            ExerciseTestCase(
                input="1",
                expected_output="1",
                is_hidden=True,
            ),
            ExerciseTestCase(
                input="2",
                expected_output="2",
                is_hidden=True,
            ),
            ExerciseTestCase(
                input="3",
                expected_output="3",
                is_hidden=True,
            ),
            ExerciseTestCase(
                input="4",
                expected_output="4",
                is_hidden=True,
            ),
        ],
    )

    with pytest.raises(
        ExerciseValidationError,
        match="1 or 2 public sample test cases",
    ):
        validator.validate(request, exercise)


def test_validate_rejects_more_than_two_public_test_cases() -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    exercise = ExerciseResponse(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
        statement="Enunț valid.",
        solution=VALID_CPP_SOLUTION,
        explanation="Explicație validă.",
        test_cases=[
            ExerciseTestCase(
                input="1",
                expected_output="1",
                is_hidden=False,
            ),
            ExerciseTestCase(
                input="2",
                expected_output="2",
                is_hidden=False,
            ),
            ExerciseTestCase(
                input="3",
                expected_output="3",
                is_hidden=False,
            ),
            ExerciseTestCase(
                input="4",
                expected_output="4",
                is_hidden=True,
            ),
        ],
    )

    with pytest.raises(
        ExerciseValidationError,
        match="1 or 2 public sample test cases",
    ):
        validator.validate(request, exercise)


def test_validate_rejects_duplicate_test_cases() -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)

    request = ExerciseRequest(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
    )

    exercise = ExerciseResponse(
        topic="vectori",
        difficulty=Difficulty.MEDIUM,
        statement="Enunț valid.",
        solution=VALID_CPP_SOLUTION,
        explanation="Explicație validă.",
        test_cases=[
            ExerciseTestCase(
                input="1",
                expected_output="1",
                is_hidden=False,
            ),
            ExerciseTestCase(
                input="2",
                expected_output="2",
                is_hidden=True,
            ),
            ExerciseTestCase(
                input="2",
                expected_output="2",
                is_hidden=True,
            ),
            ExerciseTestCase(
                input="4",
                expected_output="4",
                is_hidden=True,
            ),
        ],
    )

    with pytest.raises(
        ExerciseValidationError,
        match="duplicate test cases",
    ):
        validator.validate(request, exercise)


def _exercise_with_solution(
    solution: str,
    *,
    topic: str = "files",
) -> tuple[ExerciseRequest, ExerciseResponse]:
    request = ExerciseRequest(topic=topic, difficulty=Difficulty.MEDIUM)
    exercise = ExerciseResponse(
        topic=topic,
        difficulty=Difficulty.MEDIUM,
        statement="Enunț Bac valid.",
        solution=solution,
        explanation="Explicație validă.",
        test_cases=build_valid_test_cases(),
    )
    return request, exercise


def test_validate_rejects_reference_solution_without_main() -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)
    request, exercise = _exercise_with_solution(
        "int suma(int a, int b) { return a + b; }",
        topic="subprograms",
    )

    with pytest.raises(
        ExerciseValidationError,
        match=r"complete C\+\+17 program.*main\(\)",
    ):
        validator.validate(request, exercise)

    assert code_validator.test_case_validation_calls == 0


@pytest.mark.parametrize(
    "forbidden_solution",
    [
        '#include <fstream>\nint main(){ std::ifstream f("bac.txt"); }',
        '#include <fstream>\nint main(){ std::ofstream f("out.txt"); }',
        '#include <fstream>\nint main(){ std::fstream f("data.txt"); }',
        '#include <cstdio>\nint main(){ freopen("bac.txt", "r", stdin); }',
        'int main(){ stream.open("input.txt"); }',
        'int main(){ const char* source = "bac.txt"; return source[0]; }',
    ],
)
def test_validate_rejects_named_file_io(forbidden_solution: str) -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)
    request, exercise = _exercise_with_solution(forbidden_solution)

    with pytest.raises(
        ExerciseValidationError,
        match="standard input.*standard output",
    ):
        validator.validate(request, exercise)

    assert code_validator.test_case_validation_calls == 0


def test_validate_accepts_subprogram_with_complete_main_harness() -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)
    request, exercise = _exercise_with_solution(
        """
        #include <iostream>
        int suma(int a, int b) { return a + b; }
        int main() {
            int a, b;
            std::cin >> a >> b;
            std::cout << suma(a, b);
            return 0;
        }
        """,
        topic="subprograms",
    )

    validator.validate(request, exercise)

    assert code_validator.test_case_validation_calls == 1


def test_validate_rejects_oversized_bac_response_before_compilation() -> None:
    code_validator = FakeCodeValidator()
    validator = ExerciseValidator(code_validator)
    request, exercise = _exercise_with_solution(VALID_CPP_SOLUTION)
    exercise.explanation = "x" * 1801

    with pytest.raises(
        ExerciseValidationError,
        match="explanation.*1800-character Bac-size limit",
    ):
        validator.validate(request, exercise)

    assert code_validator.test_case_validation_calls == 0

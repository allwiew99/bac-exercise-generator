from bac_generator.schemas.exercise import ExerciseTestCase
from bac_generator.schemas.submission import SubmissionStatus
from bac_generator.services.submission_evaluator import SubmissionEvaluator


def test_submission_evaluator_returns_passed() -> None:
    evaluator = SubmissionEvaluator()

    code = """
#include <iostream>
using namespace std;

int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b;
    return 0;
}
"""

    test_cases = [
        ExerciseTestCase(
            input="1 2",
            expected_output="3",
        ),
        ExerciseTestCase(
            input="10 5",
            expected_output="15",
        ),
    ]

    result = evaluator.evaluate(
        code,
        test_cases,
    )

    assert result.score == 100
    assert result.passed_tests == 2
    assert result.total_tests == 2
    assert result.status is SubmissionStatus.PASSED


def test_submission_evaluator_returns_partial() -> None:
    evaluator = SubmissionEvaluator()

    code = """
#include <iostream>
using namespace std;

int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b;
    return 0;
}
"""

    test_cases = [
        ExerciseTestCase(
            input="1 2",
            expected_output="3",
        ),
        ExerciseTestCase(
            input="10 5",
            expected_output="999",
        ),
    ]

    result = evaluator.evaluate(
        code,
        test_cases,
    )

    assert result.score == 50
    assert result.passed_tests == 1
    assert result.total_tests == 2
    assert result.status is SubmissionStatus.PARTIAL


def test_submission_evaluator_returns_failed() -> None:
    evaluator = SubmissionEvaluator()

    code = """
#include <iostream>
using namespace std;

int main() {
    cout << 0;
    return 0;
}
"""

    test_cases = [
        ExerciseTestCase(
            input="1 2",
            expected_output="3",
        ),
        ExerciseTestCase(
            input="10 5",
            expected_output="15",
        ),
    ]

    result = evaluator.evaluate(
        code,
        test_cases,
    )

    assert result.score == 0
    assert result.passed_tests == 0
    assert result.total_tests == 2
    assert result.status is SubmissionStatus.FAILED


def test_submission_evaluator_returns_compilation_error() -> None:
    evaluator = SubmissionEvaluator()

    code = """
#include <iostream>

int main() {
    this is invalid c++
}
"""

    test_cases = [
        ExerciseTestCase(
            input="1 2",
            expected_output="3",
        ),
    ]

    result = evaluator.evaluate(
        code,
        test_cases,
    )

    assert result.score == 0
    assert result.passed_tests == 0
    assert result.total_tests == 1
    assert result.status is SubmissionStatus.COMPILATION_ERROR
    assert result.feedback


def test_submission_evaluator_returns_runtime_error() -> None:
    evaluator = SubmissionEvaluator()

    code = """
#include <iostream>
using namespace std;

int main() {
    int* p = nullptr;
    cout << *p;
    return 0;
}
"""

    test_cases = [
        ExerciseTestCase(
            input="1",
            expected_output="1",
        ),
    ]

    result = evaluator.evaluate(
        code,
        test_cases,
    )

    assert result.score == 0
    assert result.passed_tests == 0
    assert result.total_tests == 1
    assert result.status is SubmissionStatus.RUNTIME_ERROR


def test_submission_evaluator_rejects_empty_code() -> None:
    evaluator = SubmissionEvaluator()

    test_cases = [
        ExerciseTestCase(
            input="1",
            expected_output="1",
        ),
    ]

    result = evaluator.evaluate(
        "",
        test_cases,
    )

    assert result.score == 0
    assert result.status is SubmissionStatus.COMPILATION_ERROR
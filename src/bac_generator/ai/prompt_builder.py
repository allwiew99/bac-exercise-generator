from bac_generator.schemas.exercise import ExerciseRequest, ExerciseResponse


class PromptBuilder:
    def build_exercise_prompt(
        self,
        request: ExerciseRequest,
        context: str = "",
    ) -> str:
        reference_context = ""

        if context:
            reference_context = f"""
Reference context from validated Romanian Baccalaureate material:

{context}

Use the reference material only to understand:
- the expected Baccalaureate style,
- the requested topic,
- the approximate difficulty,
- common exercise structures.

Do not copy or closely reproduce any reference exercise.
Generate a genuinely new exercise.
Do not copy solutions, wording, constants, examples, or test cases
from the reference material.
"""

        return f"""
Task:
Generate a Romanian Baccalaureate computer science exercise.

Topic:
{request.topic}

Difficulty:
{request.difficulty}

{reference_context}

Requirements:

- Generate a clear and correct problem statement.
- The exercise must genuinely match the requested difficulty.
- The "solution" field must be a complete C++17 program with exactly one
  int main() entry point, even when the statement asks for a subprogram.
- The complete program must read every input value from standard input (stdin)
  and write only the requested answer to standard output (stdout).
- Never use ifstream, ofstream, fstream, freopen, .open(...), hard-coded input
  or output filenames, or any other named files.
- For topic "files", keep the Bac file-processing concept, but state clearly
  that the conceptual file contents are supplied through standard input.
- For topic "subprograms", preserve a Bac-style student-facing statement that
  asks for the subprogram, while the reference solution also includes a small
  main() harness that reads its parameters, invokes the requested subprogram,
  and prints its observable result or modified values.
- Include a clear explanation of the solution.
- Keep the statement self-contained and concise.
- Limit the explanation to the algorithm, correctness, and complexity.
- Keep the C++17 solution complete but compact; do not repeat the statement.
- Keep the entire JSON response comfortably within 8,192 output tokens.
- Apply these strict per-field bounds:
  statement: at most 1,800 characters;
  solution: at most 5,000 characters;
  explanation: at most 1,800 characters;
  each test-case input or expected_output: at most 500 characters.
- Use compact, human-auditable test data. Never emit large arrays, matrices,
  graphs, files, or repeated values merely to demonstrate an upper bound.
- Do not include manual execution traces, long enumerations, or step-by-step
  calculations in the explanation; summarize correctness in a short paragraph.
- Generate between 4 and 6 test cases.
- Exactly 1 or 2 test cases must be public sample test cases.
- Public sample test cases must have:
  "is_hidden": false
- All remaining test cases must be hidden and must have:
  "is_hidden": true
- Public sample test cases should be simple and illustrative enough
  to help the student understand the input/output format.
- Hidden test cases should provide stronger validation and should
  include relevant edge cases when appropriate.
- Test cases should not be duplicates of each other.
- Every test case must contain exactly three fields:
  "input", "expected_output", and "is_hidden".
- "input" must be a string.
- "expected_output" must be a string.
- "is_hidden" must be a JSON boolean.
- The expected output of every test case must match the provided
  C++ solution.

Output:

- Return only one valid JSON object.
- Use exactly these six top-level keys:
  "topic",
  "difficulty",
  "statement",
  "solution",
  "explanation",
  "test_cases".
- "test_cases" must be an array containing between 4 and 6 objects.
- Each test case object must contain exactly these three keys:
  "input",
  "expected_output",
  "is_hidden".
- Exactly 1 or 2 test cases must have "is_hidden": false.
- All remaining test cases must have "is_hidden": true.
- Do not rename any key.
- Do not use "problem", "problem_statement", "answer",
  or other alternative keys.
- Copy the requested topic exactly into "topic".
- Copy the requested difficulty exactly into "difficulty".
- Do not use Markdown or code fences.
- Do not add text before or after the JSON object.
        """.strip()

    def build_repair_prompt(
        self,
        request: ExerciseRequest,
        previous_error: str,
        context: str = "",
        previous_response: ExerciseResponse | None = None,
    ) -> str:
        base_prompt = self.build_exercise_prompt(
            request,
            context=context,
        )

        candidate_section = ""
        if previous_response is not None:
            candidate_section = f"""
Repair this exact candidate instead of inventing a different exercise:
{previous_response.model_dump_json()}
"""

        targeted_correction = ""
        if "Program output does not match expected output" in previous_error:
            targeted_correction = """
The validator executed the program and supplied authoritative Expected and
Actual values plus the exact Input. For this repair, change only the
expected_output belonging to that matching Input to
use the reported Actual value. Do not alter the statement, solution, explanation,
inputs, visibility flags, or any other expected_output.
"""

        return f"""
{base_prompt}

The previous attempt was invalid.

Reason:
{previous_error}

{candidate_section}

{targeted_correction}

Correction requirements:

- Fix the reported issue.
- When an exact candidate is supplied, preserve its valid fields and make the
  smallest correction needed. Follow any targeted correction above exactly.
- Keep the requested topic unchanged.
- Keep the requested difficulty unchanged.
- Return only one valid JSON object.
- Use exactly these six top-level keys:
  "topic",
  "difficulty",
  "statement",
  "solution",
  "explanation",
  "test_cases".
- "test_cases" must contain between 4 and 6 objects.
- Every test case must contain exactly:
  "input",
  "expected_output",
  "is_hidden".
- Exactly 1 or 2 test cases must have "is_hidden": false.
- All remaining test cases must have "is_hidden": true.
- "input" and "expected_output" must be strings.
- "is_hidden" must be a JSON boolean.
- The expected output of every test case must match the corrected
  C++ solution.
- Do not add Markdown or code fences.
- Do not add text before or after the JSON object.
        """.strip()

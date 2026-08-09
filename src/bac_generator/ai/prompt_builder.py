from bac_generator.schemas.exercise import ExerciseRequest


class PromptBuilder:
    def build_exercise_prompt(
        self,
        request: ExerciseRequest,
    ) -> str:
        return f"""
Task:
Generate a Romanian Baccalaureate computer science exercise.

Topic:
{request.topic}

Difficulty:
{request.difficulty}

Requirements:

- Generate a clear and correct problem statement.
- The exercise must genuinely match the requested difficulty.
- Include the complete C++ solution.
- Include a clear explanation of the solution.
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
    ) -> str:
        base_prompt = self.build_exercise_prompt(request)

        return f"""
{base_prompt}

The previous attempt was invalid.

Reason:
{previous_error}

Correction requirements:

- Fix the reported issue.
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
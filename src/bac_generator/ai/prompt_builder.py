from bac_generator.schemas.exercise import ExerciseRequest


class PromptBuilder:
    def build_exercise_prompt(self, request: ExerciseRequest) -> str:
        return f"""
Task:
Generate a Romanian Baccalaureate computer science exercise.

Topic:
{request.topic}

Difficulty:
{request.difficulty}

Requirements:
- Generate a clear and correct problem statement.
- Include the complete solution.
- Include an explanation of the solution.

Output:
- Return only one valid JSON object.
- Use exactly these five keys:
  "topic", "difficulty", "statement", "solution", "explanation".
- Do not rename any key.
- Do not use "problem", "problem_statement", "answer" or other alternative keys.
- Copy the requested topic into "topic".
- Copy the requested difficulty into "difficulty".
- The value of "difficulty" must be exactly "easy", "medium" or "hard".
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
    - Use exactly these five keys:
      "topic", "difficulty", "statement", "solution", "explanation".
    - Do not add Markdown or code fences.
    - Do not add text before or after the JSON object.
    """.strip()

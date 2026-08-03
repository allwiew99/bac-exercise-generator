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
Return a JSON object with these fields:
topic, difficulty, statement, solution, explanation.
""".strip()
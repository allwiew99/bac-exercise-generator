from bac_generator.schemas.exercise import ExerciseRequest, ExerciseResponse


class ExerciseService:
    def generate(self, request: ExerciseRequest) -> ExerciseResponse:
        return ExerciseResponse(
            topic=request.topic,
            difficulty=request.difficulty,
            statement=(
                f"Se citește un {request.topic}. "
                f"Determină o soluție pentru o problemă de dificultate "
                f"{request.difficulty}."
            ),
            solution="Aceasta este soluția problemei.",
            explanation="Aceasta este explicația problemei.",
        )
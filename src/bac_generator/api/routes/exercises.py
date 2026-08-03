from fastapi import APIRouter

from bac_generator.schemas.exercise import ExerciseRequest, ExerciseResponse
from bac_generator.services.exercise_service import ExerciseService

router = APIRouter(
    prefix="/exercises",
    tags=["exercises"],
)


@router.post(
    "/generate",
    response_model=ExerciseResponse,
)
def generate_exercise(request: ExerciseRequest) -> ExerciseResponse:
    service = ExerciseService()
    return service.generate(request)
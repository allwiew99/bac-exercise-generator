from enum import StrEnum

from pydantic import BaseModel


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ExerciseRequest(BaseModel):
    topic: str
    difficulty: Difficulty


class ExerciseResponse(BaseModel):
    topic: str
    difficulty: Difficulty
    statement: str
    solution: str
    explanation: str

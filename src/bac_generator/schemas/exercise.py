from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXTREME = "extreme"


class ExerciseTestCase(BaseModel):
    input: str
    expected_output: str
    is_hidden: bool = True


class ExerciseSampleTestCase(BaseModel):
    input: str
    expected_output: str


class ExerciseRequest(BaseModel):
    topic: str
    difficulty: Difficulty


class ExerciseResponse(BaseModel):
    topic: str
    difficulty: Difficulty
    statement: str
    solution: str
    explanation: str
    test_cases: list[ExerciseTestCase]


class ExerciseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic: str
    difficulty: Difficulty
    statement: str
    solution: str
    explanation: str
    created_at: datetime
    test_cases: list[ExerciseTestCase]


class ExerciseSafeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic: str
    difficulty: Difficulty
    statement: str
    created_at: datetime
    sample_test_cases: list[ExerciseSampleTestCase] = Field(
        default_factory=list
    )

    has_submitted: bool = False
    latest_score: int | None = None
    submission_count: int = 0
    completed: bool = False
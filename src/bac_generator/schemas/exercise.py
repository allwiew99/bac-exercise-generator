from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

MAX_STATEMENT_CHARS = 1800
MAX_SOLUTION_CHARS = 5000
MAX_EXPLANATION_CHARS = 1800
MAX_TEST_VALUE_CHARS = 500


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXTREME = "extreme"


class ExerciseTestCase(BaseModel):
    input: str = Field(description="At most 500 characters.")
    expected_output: str = Field(description="At most 500 characters.")
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
    statement: str = Field(description="At most 1,800 characters.")
    solution: str = Field(description="At most 5,000 characters.")
    explanation: str = Field(description="At most 1,800 characters.")
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

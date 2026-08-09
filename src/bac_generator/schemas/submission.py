from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class SubmissionStatus(StrEnum):
    PASSED = "passed"
    PARTIAL = "partial"
    FAILED = "failed"
    COMPILATION_ERROR = "compilation_error"
    RUNTIME_ERROR = "runtime_error"


class SubmissionEvaluation(BaseModel):
    score: int
    passed_tests: int
    total_tests: int
    status: SubmissionStatus
    feedback: str | None = None


class SubmissionProgress(BaseModel):
    has_submitted: bool
    latest_score: int | None
    submission_count: int
    completed: bool
    

class SubmitSolutionRequest(BaseModel):
    code: str


class SubmissionCreate(BaseModel):
    exercise_id: int
    user_id: str
    code: str
    score: int
    passed_tests: int
    total_tests: int
    status: SubmissionStatus
    feedback: str | None = None


class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exercise_id: int
    score: int
    passed_tests: int
    total_tests: int
    status: SubmissionStatus
    feedback: str | None
    created_at: datetime


class OfficialSolutionRead(BaseModel):
    solution: str
    explanation: str
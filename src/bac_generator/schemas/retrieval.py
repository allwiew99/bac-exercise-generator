from pydantic import BaseModel


class RetrievalDocument(BaseModel):
    id: str
    text: str
    source: str
    topic: str
    year: int | None = None
    bac_section: str | None = None
    exercise_type: str | None = None
    difficulty: str | None = None
    language: str = "ro"


class RetrievedChunk(BaseModel):
    id: str
    text: str
    source: str
    topic: str
    year: int | None = None
    bac_section: str | None = None
    exercise_type: str | None = None
    difficulty: str | None = None
    score: float
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Literal

from bac_generator.schemas.retrieval import RetrievalDocument

SessionKind = Literal["simulation", "model"]
Profile = Literal["MI", "SN"]
ProgrammingLanguage = Literal["C/C++", "Pascal", "C/C++ + Pascal"]


class DocumentType(StrEnum):
    SUBJECT = "subject"
    BAREM = "barem"


@dataclass(frozen=True)
class BacMetadata:
    year: int
    document_type: DocumentType
    profile: Profile
    programming_language: ProgrammingLanguage
    session: SessionKind | None = None
    variant: str | None = None
    warnings: tuple[str, ...] = ()

    @property
    def pairing_key(self) -> tuple[int, Profile, SessionKind | None, str | None]:
        return (self.year, self.profile, self.session, self.variant)


@dataclass(frozen=True)
class ExtractedPdf:
    source: Path
    pages: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    @property
    def text(self) -> str:
        return "\n".join(self.pages)


@dataclass(frozen=True)
class ParsedExercise:
    section: str
    number: int
    text: str
    topic: str = "unclassified"
    exercise_type: str = "open_response"
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParsedBaremEntry:
    section: str
    number: int
    text: str


@dataclass(frozen=True)
class ExcludedExercise:
    source: Path
    section: str
    number: int
    reason: str


@dataclass(frozen=True)
class ParsedBacDocument:
    source: Path
    metadata: BacMetadata
    exercises: tuple[ParsedExercise, ...] = ()
    excluded_exercises: tuple[ExcludedExercise, ...] = ()
    barem_entries: tuple[ParsedBaremEntry, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class PdfAuditRecord:
    source: Path
    extraction_works: bool
    parsing_reliable: bool
    skipped: bool
    metadata: BacMetadata | None = None
    exercise_count: int = 0
    excluded_exercise_count: int = 0
    barem_entry_count: int = 0
    warnings: tuple[str, ...] = ()


@dataclass
class BuildResult:
    documents: list[RetrievalDocument] = field(default_factory=list)
    parsed_bareme: list[ParsedBacDocument] = field(default_factory=list)
    excluded_exercises: list[ExcludedExercise] = field(default_factory=list)
    audit_records: list[PdfAuditRecord] = field(default_factory=list)

    @property
    def pdfs_scanned(self) -> int:
        return len(self.audit_records)

    @property
    def pdfs_parsed(self) -> int:
        return sum(not record.skipped for record in self.audit_records)

    @property
    def pdfs_skipped(self) -> int:
        return sum(record.skipped for record in self.audit_records)

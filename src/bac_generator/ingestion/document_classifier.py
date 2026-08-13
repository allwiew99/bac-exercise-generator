import re
import unicodedata
from pathlib import Path
from typing import cast

from bac_generator.ingestion.models import (
    BacMetadata,
    DocumentType,
    Profile,
    ProgrammingLanguage,
    SessionKind,
)


class DocumentClassificationError(ValueError):
    """Raised when required Bac metadata cannot be established from content."""


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def classify_document(text: str, source: Path) -> BacMetadata:
    """Classify a Bac PDF from its content; the filename is diagnostic only."""
    header = text[:2500]
    folded = _fold(header)
    missing: list[str] = []

    year_match = re.search(r"bacalaureat(?:ul)? national\s+(20\d{2})", folded)
    if year_match is None:
        missing.append("year")

    if "barem de evaluare" in folded:
        document_type = DocumentType.BAREM
    elif "toate subiectele sunt obligatorii" in folded:
        document_type = DocumentType.SUBJECT
    else:
        missing.append("document type")
        document_type = DocumentType.SUBJECT

    if "stiinte ale naturii" in folded:
        profile: Profile = "SN"
    elif "matematica-informatica" in folded:
        profile = "MI"
    else:
        missing.append("profile")
        profile = "MI"

    if document_type is DocumentType.BAREM and "comun pentru limbajele c/c++" in folded:
        programming_language: ProgrammingLanguage = "C/C++ + Pascal"
    elif "limbajul c/c++" in folded:
        programming_language = "C/C++"
    elif "limbajul pascal" in folded:
        programming_language = "Pascal"
    else:
        missing.append("programming language")
        programming_language = "C/C++"

    session: SessionKind | None
    if re.search(r"\bsimulare\b", folded):
        session = "simulation"
    elif re.search(r"\bmodel\b", folded):
        session = "model"
    else:
        session = None

    variant_match = re.search(r"varianta\s+(\d+)", folded)
    variant = variant_match.group(1) if variant_match else None
    if session is None and variant is None:
        missing.append("variant")

    if missing:
        fields = ", ".join(missing)
        raise DocumentClassificationError(f"{source.name}: missing or ambiguous {fields}")

    warnings = () if session is not None else ("exam session is not stated in the PDF",)
    return BacMetadata(
        year=int(cast(re.Match[str], year_match).group(1)),
        document_type=document_type,
        profile=profile,
        programming_language=programming_language,
        session=session,
        variant=variant,
        warnings=warnings,
    )

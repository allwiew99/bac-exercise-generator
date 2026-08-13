import re
import unicodedata
from pathlib import Path

from bac_generator.ingestion.models import (
    BacMetadata,
    ExcludedExercise,
    ParsedBacDocument,
    ParsedExercise,
)
from bac_generator.ingestion.safety import exercise_exclusion_reason

_SECTION_PATTERN = re.compile(
    r"(?im)^[ \t]*SUBIECTUL\s+(?:(?:al)\s+)?(?P<section>III|II|I)"
    r"(?:\s*[-–]\s*lea)?(?:\s*\([^\n)]*\))?[ \t]*$"
)
_ITEM_PATTERN = re.compile(r"(?m)^[ \t]*(?P<number>[1-9])\.\s+")
_EXPECTED_COUNTS = {
    "legacy": {"I": 2, "II": 5, "III": 4},
    "modern": {"I": 5, "II": 3, "III": 3},
}
_SHARED_SECTION_INSTRUCTIONS = {
    "scrieti pe foaia de examen raspunsul pentru fiecare dintre cerintele urmatoare."
}


class ExerciseParsingError(ValueError):
    """Raised when semantic exercise boundaries are not reliable."""


def _fold_line(line: str) -> str:
    return (
        unicodedata.normalize("NFKD", line)
        .encode("ascii", "ignore")
        .decode()
        .casefold()
        .strip()
    )


def _remove_shared_section_instructions(body: str) -> str:
    return "\n".join(
        line
        for line in body.splitlines()
        if _fold_line(line) not in _SHARED_SECTION_INSTRUCTIONS
    )


def expected_section_counts(year: int, profile: str) -> dict[str, int]:
    if 2016 <= year <= 2018:
        if profile == "SN":
            return {"I": 2, "II": 4, "III": 4}
        return _EXPECTED_COUNTS["legacy"]
    if 2019 <= year <= 2020:
        return _EXPECTED_COUNTS["modern"]
    raise ExerciseParsingError(f"unsupported Bac layout year: {year}")


def split_sections(text: str) -> dict[str, str]:
    matches = list(_SECTION_PATTERN.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        section = match.group("section")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        if section in sections:
            raise ExerciseParsingError(f"duplicate section marker: {section}")
        sections[section] = text[match.end() : end].strip()
    if set(sections) != {"I", "II", "III"}:
        found = ", ".join(sections) or "none"
        raise ExerciseParsingError(f"expected sections I, II, III; found {found}")
    return sections


def split_numbered_items(body: str) -> list[tuple[int, str]]:
    body = _remove_shared_section_instructions(body)
    matches = list(_ITEM_PATTERN.finditer(body))
    items: list[tuple[int, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        number = int(match.group("number"))
        item_text = body[match.start() : end].strip()
        items.append((number, item_text))
    return items


def parse_subject(text: str, metadata: BacMetadata, source: Path) -> ParsedBacDocument:
    sections = split_sections(text)
    expected = expected_section_counts(metadata.year, metadata.profile)
    exercises: list[ParsedExercise] = []
    excluded_exercises: list[ExcludedExercise] = []

    for section in ("I", "II", "III"):
        items = split_numbered_items(sections[section])
        expected_count = expected[section]
        if len(items) != expected_count:
            raise ExerciseParsingError(
                f"{source.name}: expected {expected_count} exercises in section {section}, "
                f"found {len(items)}"
            )
        expected_numbers = list(range(1, expected_count + 1))
        actual_numbers = [number for number, _ in items]
        if actual_numbers != expected_numbers:
            raise ExerciseParsingError(
                f"{source.name}: non-sequential exercises in section {section}: {actual_numbers}"
            )
        for number, item_text in items:
            exclusion_reason = exercise_exclusion_reason(item_text)
            if exclusion_reason is not None:
                excluded_exercises.append(
                    ExcludedExercise(
                        source=source,
                        section=section,
                        number=number,
                        reason=exclusion_reason,
                    )
                )
                continue
            exercises.append(ParsedExercise(section=section, number=number, text=item_text))

    return ParsedBacDocument(
        source=source,
        metadata=metadata,
        exercises=tuple(exercises),
        excluded_exercises=tuple(excluded_exercises),
    )

import re
from pathlib import Path

from bac_generator.ingestion.exercise_parser import (
    ExerciseParsingError,
    expected_section_counts,
    split_numbered_items,
    split_sections,
)
from bac_generator.ingestion.models import BacMetadata, ParsedBacDocument, ParsedBaremEntry

_COMPACT_ANSWER_PATTERN = re.compile(r"(?<!\d)(?P<number>[1-9])\s*(?P<answer>[a-d])(?=\s|$)")


class BaremParsingError(ValueError):
    """Raised when grading-guide entries cannot be mapped reliably."""


def _compact_answers(body: str, expected_count: int) -> list[tuple[int, str]]:
    matches = list(_COMPACT_ANSWER_PATTERN.finditer(body))
    if len(matches) != expected_count:
        return []
    return [
        (int(match.group("number")), f"Răspuns: {match.group('answer')}") for match in matches
    ]


def parse_barem(text: str, metadata: BacMetadata, source: Path) -> ParsedBacDocument:
    try:
        sections = split_sections(text)
        expected = expected_section_counts(metadata.year, metadata.profile)
    except ExerciseParsingError as exc:
        raise BaremParsingError(str(exc)) from exc

    entries: list[ParsedBaremEntry] = []
    for section in ("I", "II", "III"):
        expected_count = expected[section]
        items = split_numbered_items(sections[section])
        if len(items) != expected_count and section == "I":
            items = _compact_answers(sections[section], expected_count)
        if len(items) != expected_count:
            raise BaremParsingError(
                f"{source.name}: expected {expected_count} barem entries in section {section}, "
                f"found {len(items)}"
            )
        numbers = [number for number, _ in items]
        if numbers != list(range(1, expected_count + 1)):
            raise BaremParsingError(
                f"{source.name}: non-sequential barem entries in section {section}: {numbers}"
            )
        entries.extend(
            ParsedBaremEntry(section=section, number=number, text=item_text)
            for number, item_text in items
        )

    return ParsedBacDocument(source=source, metadata=metadata, barem_entries=tuple(entries))

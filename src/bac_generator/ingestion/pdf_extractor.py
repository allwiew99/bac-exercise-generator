import re
from pathlib import Path
from typing import Any

import pdfplumber
from pdfplumber.page import Page
from pdfplumber.utils.text import extract_text, extract_words

from bac_generator.ingestion.models import ExtractedPdf
from bac_generator.ingestion.safety import (
    AMBIGUOUS_MATH_NOTATION_MARKER,
    UNRELIABLE_PSEUDOCODE_LAYOUT_MARKER,
)

PdfChar = dict[str, Any]

_FOOTER_NUMBER_PATTERN = re.compile(r"\d{1,3}")
_SCRIPT_SIZE_RATIO = 0.8
_SCRIPT_OFFSET_RATIO = 0.25
_FOOTER_TOP_RATIO = 0.9
_FOOTER_CENTER_TOLERANCE_RATIO = 0.1
_PSEUDOCODE_ITEM_PATTERN = re.compile(r"[1-9]\.")
_PSEUDOCODE_STRUCTURE_GLYPHS = frozenset("┌│└■")
_TEXT_X_TOLERANCE = 2
_TEXT_Y_TOLERANCE = 3


class PdfExtractionError(ValueError):
    """Raised when a PDF cannot provide reliable text."""


def _vertical_script_relation(char: PdfChar, base: PdfChar) -> str | None:
    char_size = float(char["size"])
    base_size = float(base["size"])
    if char_size > base_size * _SCRIPT_SIZE_RATIO:
        return None
    if float(base["bottom"]) - float(char["bottom"]) >= base_size * _SCRIPT_OFFSET_RATIO:
        return "^"
    if float(char["top"]) - float(base["top"]) >= base_size * _SCRIPT_OFFSET_RATIO:
        return "_"
    return None


def _script_relation(char: PdfChar, base: PdfChar) -> str | None:
    gap = float(char["x0"]) - float(base["x1"])
    if gap < -0.5 or gap > float(base["size"]) * 0.75:
        return None
    return _vertical_script_relation(char, base)


def _is_ambiguous_script_candidate(char: PdfChar, base: PdfChar) -> bool:
    gap = float(char["x0"]) - float(base["x1"])
    return (
        float(char["size"]) <= float(base["size"]) * _SCRIPT_SIZE_RATIO
        and -0.5 <= gap <= float(base["size"]) * 0.75
        and re.fullmatch(r"[A-Za-z0-9+-]+", str(char["text"])) is not None
    )


def _align_script_char(char: PdfChar, base: PdfChar) -> None:
    for key in ("top", "bottom", "doctop", "y0", "y1", "height"):
        if key in base:
            char[key] = base[key]


def _reconstruct_script_runs(chars: list[PdfChar]) -> list[PdfChar]:
    source = [dict(char) for char in chars]
    reconstructed: list[PdfChar] = []
    base: PdfChar | None = None
    index = 0

    while index < len(source):
        char = source[index]
        relation = _script_relation(char, base) if base is not None else None
        if relation is not None and char["text"].strip():
            assert base is not None
            run = [char]
            next_index = index + 1
            while next_index < len(source):
                candidate = source[next_index]
                candidate_relation = _vertical_script_relation(candidate, base)
                gap = float(candidate["x0"]) - float(run[-1]["x1"])
                if (
                    candidate_relation != relation
                    or not candidate["text"].strip()
                    or gap > float(base["size"]) * 0.5
                ):
                    break
                run.append(candidate)
                next_index += 1

            script_text = "".join(str(item["text"]) for item in run)
            if len(run) > 1:
                script_text = f"{{{script_text}}}"
            char["text"] = f"{relation}{script_text}"
            char["x1"] = run[-1]["x1"]
            char["width"] = float(char["x1"]) - float(char["x0"])
            if "adv" in char:
                char["adv"] = char["width"]
            _align_script_char(char, base)
            reconstructed.append(char)
            index = next_index
            continue

        reconstructed.append(char)
        if (
            base is not None
            and relation is None
            and _is_ambiguous_script_candidate(char, base)
        ):
            char["text"] = f"{AMBIGUOUS_MATH_NOTATION_MARKER}{char['text']}"
        if char["text"].strip():
            base = char
        index += 1

    return reconstructed


def _without_footer_page_numbers(
    chars: list[PdfChar], page_width: float, page_height: float
) -> list[PdfChar]:
    words = extract_words(chars, x_tolerance=2, y_tolerance=3)
    footer_boxes: list[tuple[float, float, float, float]] = []

    for word in words:
        if _FOOTER_NUMBER_PATTERN.fullmatch(str(word["text"])) is None:
            continue
        if float(word["top"]) < page_height * _FOOTER_TOP_RATIO:
            continue
        center = (float(word["x0"]) + float(word["x1"])) / 2
        if abs(center - page_width / 2) > page_width * _FOOTER_CENTER_TOLERANCE_RATIO:
            continue
        same_line = [
            other
            for other in words
            if abs(float(other["top"]) - float(word["top"])) <= 2
        ]
        if len(same_line) == 1:
            footer_boxes.append(
                (
                    float(word["x0"]),
                    float(word["top"]),
                    float(word["x1"]),
                    float(word["bottom"]),
                )
            )

    def is_footer_char(char: PdfChar) -> bool:
        return any(
            float(char["x0"]) >= x0 - 0.5
            and float(char["x1"]) <= x1 + 0.5
            and float(char["top"]) >= top - 0.5
            and float(char["bottom"]) <= bottom + 0.5
            for x0, top, x1, bottom in footer_boxes
        )

    return [char for char in chars if not is_footer_char(char)]


def _extract_chars(chars: list[PdfChar], *, layout: bool) -> str:
    if not chars:
        return ""
    return extract_text(
        chars,
        layout=layout,
        x_tolerance=_TEXT_X_TOLERANCE,
        y_tolerance=_TEXT_Y_TOLERANCE,
    ).strip()


def _cluster_chars_by_line(chars: list[PdfChar]) -> list[list[PdfChar]]:
    lines: list[list[PdfChar]] = []
    line_top: float | None = None
    for char in sorted(chars, key=lambda item: (float(item["top"]), float(item["x0"]))):
        top = float(char["top"])
        if line_top is None or abs(top - line_top) > _TEXT_Y_TOLERANCE:
            lines.append([char])
            line_top = top
        else:
            lines[-1].append(char)
    return lines


def _is_code_font(char: PdfChar) -> bool:
    font_name = str(char.get("fontname", "")).casefold()
    return "courier" in font_name or "wingdings" in font_name


def _is_control_glyph(char: PdfChar) -> bool:
    font_name = str(char.get("fontname", "")).casefold()
    text = str(char["text"])
    return (
        "wingdings" in font_name
        or "symbol" in font_name
        or text == "‹"
        or text.startswith("(cid:")
        or any(glyph in text for glyph in _PSEUDOCODE_STRUCTURE_GLYPHS)
    )


def _partition_pseudocode_block(
    chars: list[PdfChar], code_x: float
) -> tuple[list[PdfChar], list[PdfChar]]:
    left: list[PdfChar] = []
    right: list[PdfChar] = []

    for line in _cluster_chars_by_line(chars):
        ordered = sorted(line, key=lambda char: float(char["x0"]))
        right_side = [
            char
            for char in ordered
            if (float(char["x0"]) + float(char["x1"])) / 2 >= code_x
        ]
        visible_right = [char for char in right_side if str(char["text"]).strip()]
        code_anchors = [
            char
            for char in visible_right
            if _is_code_font(char)
            or any(glyph in str(char["text"]) for glyph in _PSEUDOCODE_STRUCTURE_GLYPHS)
        ]
        anchor_x = min((float(char["x0"]) for char in code_anchors), default=None)
        right_text = "".join(str(char["text"]) for char in right_side).strip()
        parenthesized_annotation = right_text.startswith("(") and "num" in right_text.casefold()

        if anchor_x is not None and anchor_x <= code_x + 20:
            preceding_controls = [
                char
                for char in ordered
                if _is_control_glyph(char)
                and anchor_x - 12 <= float(char["x0"]) < anchor_x
            ]
            block_start_x = min(
                (float(char["x0"]) for char in preceding_controls),
                default=anchor_x,
            )
            left.extend(char for char in ordered if float(char["x0"]) < block_start_x)
            right.extend(char for char in ordered if float(char["x0"]) >= block_start_x)
        elif parenthesized_annotation:
            left.extend(char for char in ordered if char not in right_side)
            right.extend(right_side)
        else:
            orphan_controls = [char for char in right_side if _is_control_glyph(char)]
            left.extend(char for char in ordered if char not in orphan_controls)
            right.extend(orphan_controls)

    return left, right


def _linearize_side_by_side_pseudocode(chars: list[PdfChar], page_width: float) -> str | None:
    words = extract_words(chars, x_tolerance=2, y_tolerance=3)
    pseudocode_words = [
        word for word in words if "pseudocod" in str(word["text"]).casefold()
    ]

    for pseudocode_word in pseudocode_words:
        pseudocode_top = float(pseudocode_word["top"])
        pseudocode_x = float(pseudocode_word["x0"])
        introduces_algorithm = any(
            str(word["text"]).casefold().startswith("algoritm")
            and pseudocode_top - 25 <= float(word["top"]) <= pseudocode_top + 2
            and (
                float(word["top"]) < pseudocode_top - 2
                or float(word["x0"]) < pseudocode_x
            )
            for word in words
        )
        if not introduces_algorithm:
            continue

        structures = [
            char
            for char in chars
            if any(glyph in str(char["text"]) for glyph in _PSEUDOCODE_STRUCTURE_GLYPHS)
            and float(char["x0"]) > page_width * 0.45
            and pseudocode_top - 30 <= float(char["top"]) <= pseudocode_top + 260
        ]
        if not structures:
            continue

        item_words = [
            word
            for word in words
            if _PSEUDOCODE_ITEM_PATTERN.fullmatch(str(word["text"])) is not None
            and float(word["x0"]) < page_width * 0.25
            and pseudocode_top - 45 <= float(word["top"]) <= pseudocode_top
        ]
        if not item_words:
            return f"{_extract_chars(chars, layout=True)}\n{UNRELIABLE_PSEUDOCODE_LAYOUT_MARKER}"

        item_word = max(item_words, key=lambda word: float(word["top"]))
        block_top = float(item_word["top"]) - 2
        code_x = min(float(char["x0"]) for char in structures)
        block_bottom = max(float(char["bottom"]) for char in structures) + 25

        before: list[PdfChar] = []
        block: list[PdfChar] = []
        after: list[PdfChar] = []
        for char in chars:
            vertical_center = (float(char["top"]) + float(char["bottom"])) / 2
            if vertical_center < block_top:
                before.append(char)
            elif vertical_center > block_bottom:
                after.append(char)
            else:
                block.append(char)

        left, right = _partition_pseudocode_block(block, code_x)

        left_lines = _extract_chars(left, layout=False).splitlines()
        subquestion_index = next(
            (
                index
                for index, line in enumerate(left_lines)
                if re.match(r"\s*a[.)]\s+", line)
            ),
            None,
        )
        code_text = _extract_chars(right, layout=False)
        if subquestion_index is None or not code_text:
            return f"{_extract_chars(chars, layout=True)}\n{UNRELIABLE_PSEUDOCODE_LAYOUT_MARKER}"

        left_intro = "\n".join(left_lines[:subquestion_index]).strip()
        left_questions = "\n".join(left_lines[subquestion_index:]).strip()
        parts = (
            _extract_chars(before, layout=True),
            left_intro,
            f"Pseudocod:\n{code_text}",
            left_questions,
            _extract_chars(after, layout=True),
        )
        return "\n\n".join(part for part in parts if part)

    return None


def _extract_page_text(page: Page) -> str:
    deduplicated = page.dedupe_chars(
        tolerance=0.7,
        extra_attrs=("fontname", "size"),
    )
    chars = _reconstruct_script_runs([dict(char) for char in deduplicated.chars])
    chars = _without_footer_page_numbers(chars, float(page.width), float(page.height))
    linearized = _linearize_side_by_side_pseudocode(chars, float(page.width))
    if linearized is not None:
        return linearized
    return extract_text(
        chars,
        layout=True,
        x_tolerance=_TEXT_X_TOLERANCE,
        y_tolerance=_TEXT_Y_TOLERANCE,
    )


def extract_pdf(path: Path) -> ExtractedPdf:
    """Extract page text in layout order and reject empty or malformed PDFs."""
    if not path.is_file():
        raise PdfExtractionError(f"{path}: PDF does not exist")

    try:
        with pdfplumber.open(path) as pdf:
            pages = tuple(_extract_page_text(page) for page in pdf.pages)
    except Exception as exc:
        raise PdfExtractionError(f"{path.name}: PDF extraction failed: {exc}") from exc

    if not pages:
        raise PdfExtractionError(f"{path.name}: PDF has no pages")
    empty_pages = tuple(index for index, page in enumerate(pages, start=1) if not page.strip())
    if empty_pages:
        listed = ", ".join(str(page) for page in empty_pages)
        raise PdfExtractionError(f"{path.name}: no extractable text on page(s) {listed}")
    if sum(len(page.strip()) for page in pages) < 500:
        raise PdfExtractionError(f"{path.name}: extracted text is too short to parse reliably")

    return ExtractedPdf(source=path, pages=pages)

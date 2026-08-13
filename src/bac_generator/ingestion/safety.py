import re
import unicodedata

AMBIGUOUS_MATH_NOTATION_MARKER = "⟦unsafe:ambiguous_math_notation⟧"
UNRELIABLE_PSEUDOCODE_LAYOUT_MARKER = "⟦unsafe:unreliable_pseudocode_layout⟧"

_GRAPH_TERM_PATTERN = re.compile(r"\b(?:graf|graful|arbore|arborele)\b")
_ADJACENT_VISUAL_PATTERN = re.compile(
    r"\b(?:reprezentat(?:a)?|graful|arborele)\b[^.]{0,160}\balaturat(?:a)?\b"
)
_BINARY_MATRIX_VALUE_PATTERN = re.compile(r"(?<!\d)[01](?!\d)")
_PARENT_VECTOR_PATTERN = re.compile(
    r"vector(?:ul)?\s+de\s+[\"']?tati[\"']?[^\n]{0,100}\([\d,\s-]+\)"
)
_EXPLICIT_EDGE_PATTERN = re.compile(
    r"(?:muchiile|arcele)\s+(?:sunt|grafului)[^\n]{0,120}[{(][\d,()\s-]+[})]"
)
_DIACRITIC_ONLY_LINE_PATTERN = re.compile(
    r"(?m)^\s*[ăâîșşțţĂÂÎȘŞȚŢ](?:\s+[ăâîșşțţĂÂÎȘŞȚŢ]){2,}\s*$"
)
_ALPHA_TOKEN_PATTERN = re.compile(r"[^\W\d_]+", re.UNICODE)


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def _has_textual_graph_representation(text: str, folded: str) -> bool:
    has_matrix = "matrice" in folded and len(_BINARY_MATRIX_VALUE_PATTERN.findall(text)) >= 9
    return (
        has_matrix
        or _PARENT_VECTOR_PATTERN.search(folded) is not None
        or _EXPLICIT_EDGE_PATTERN.search(folded) is not None
    )


def _has_fragmented_prose_line(text: str) -> bool:
    for line in text.splitlines():
        if re.fullmatch(
            r"[^\W\d_]+(?:\s+[^\W\d_]+)*:?", line.strip(), re.UNICODE
        ) is None:
            continue
        tokens = _ALPHA_TOKEN_PATTERN.findall(line)
        single_flags = [len(token) == 1 for token in tokens]
        single_count = sum(single_flags)
        single_runs = sum(
            is_single and (index == 0 or not single_flags[index - 1])
            for index, is_single in enumerate(single_flags)
        )
        if len(tokens) >= 8 and single_count >= 5 and single_runs >= 3:
            return True
    return False


def exercise_exclusion_reason(text: str) -> str | None:
    if AMBIGUOUS_MATH_NOTATION_MARKER in text:
        return "ambiguous_math_notation"
    if UNRELIABLE_PSEUDOCODE_LAYOUT_MARKER in text:
        return "unreliable_pseudocode_layout"
    if _DIACRITIC_ONLY_LINE_PATTERN.search(text) is not None:
        return "unreliable_text_layout"
    if _has_fragmented_prose_line(text):
        return "unreliable_text_layout"

    folded = _fold(text)
    requires_adjacent_graph_visual = (
        _GRAPH_TERM_PATTERN.search(folded) is not None
        and _ADJACENT_VISUAL_PATTERN.search(folded) is not None
    )
    if requires_adjacent_graph_visual and not _has_textual_graph_representation(text, folded):
        return "missing_required_visual"
    return None

import re
import unicodedata

_CID_PATTERN = re.compile(r"(?:\(cid:1\))+", re.IGNORECASE)
_MULTIPLICATION_CID_PATTERN = re.compile(r"(?:\(cid:215\))+", re.IGNORECASE)
_UNRESOLVED_CID_PATTERN = re.compile(r"\(cid:\d+\)", re.IGNORECASE)
_MEMBERSHIP_PATTERN = re.compile(r"˛\s*([A-Za-z])\s*˛+\s*(?=\[)")
_LESS_EQUAL_PATTERN = re.compile(r"£(?:\s*£)+")
_SWAP_PATTERN = re.compile(r"«\s*([A-Za-z]\w*)\s*«+\s*([A-Za-z]\w*)")
_REPEATED_MEMBERSHIP_PATTERN = re.compile(r"∈(?:\s*∈)+(?=\s*[\[(])")
_REPEATED_MULTIPLICATION_PATTERN = re.compile(
    r"([\w)])\s*×(?:\s*×)+(?=\s*[\w(])"
)
_PAGE_NUMBER_PATTERN = re.compile(r"^(?:Pagina\s+)?\d+\s+(?:din|/|of)\s+\d+$", re.IGNORECASE)
_BOILERPLATE_PATTERNS = (
    re.compile(r"^Ministerul Educa", re.IGNORECASE),
    re.compile(r"^Centrul Na", re.IGNORECASE),
    re.compile(r"^Examenul de bacalaureat", re.IGNORECASE),
    re.compile(r"^Probă scrisă la informatică", re.IGNORECASE),
    re.compile(r"^Barem de evaluare şi de notare$", re.IGNORECASE),
    re.compile(r"^Limbajul (?:C/C\+\+|Pascal)$", re.IGNORECASE),
    re.compile(r"^Filier[ăa] (?:teoretică|vocaţională|vocațională)", re.IGNORECASE),
)


def _is_boilerplate(line: str) -> bool:
    if _PAGE_NUMBER_PATTERN.fullmatch(line):
        return True
    return any(pattern.search(line) for pattern in _BOILERPLATE_PATTERNS)


def normalize_extracted_text(text: str) -> tuple[str, tuple[str, ...]]:
    """Normalize deterministic PDF artifacts and report anything unresolved."""
    normalized = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\u00a0", " ").replace("\u00ad", "")
    normalized = re.sub(
        r"(?im)^[ \t]*Limbajul (?:C/C\+\+|Pascal)[ \t]*\n[ \t]*[123][ \t]*(?:\n|$)",
        "",
        normalized,
    )
    normalized = _CID_PATTERN.sub(" ← ", normalized)
    normalized = _MULTIPLICATION_CID_PATTERN.sub(" × ", normalized)
    normalized = re.sub(r"‹\s+(?=[A-Za-z]\w*\s*‹)", "", normalized)
    normalized = re.sub(r"‹+", " ← ", normalized)
    normalized = normalized.replace("\uf0df", "←")
    normalized = _MEMBERSHIP_PATTERN.sub(r"\1∈", normalized)
    normalized = _REPEATED_MEMBERSHIP_PATTERN.sub("∈", normalized)
    normalized = _REPEATED_MULTIPLICATION_PATTERN.sub(r"\1 ×", normalized)
    normalized = _LESS_EQUAL_PATTERN.sub("≤", normalized)
    normalized = _SWAP_PATTERN.sub(r"\1 ↔ \2", normalized)
    normalized = re.sub(r"¨(?=\])", "", normalized)
    normalized = re.sub(r"¨+", "∪", normalized)
    lines: list[str] = []
    previous_blank = True
    for raw_line in normalized.splitlines():
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if line and _is_boilerplate(line):
            continue
        if not line:
            if not previous_blank:
                lines.append("")
            previous_blank = True
            continue
        lines.append(line)
        previous_blank = False

    while lines and not lines[-1]:
        lines.pop()

    clean_text = "\n".join(lines)
    unresolved = sorted(set(_UNRESOLVED_CID_PATTERN.findall(clean_text)))
    warnings = tuple(f"unresolved embedded-font glyph: {glyph}" for glyph in unresolved)
    return clean_text, warnings

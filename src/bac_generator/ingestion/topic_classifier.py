import re
import unicodedata

_TOPIC_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "pseudocode": (re.compile(r"\bpseudocod\b"),),
    "arrays": (re.compile(r"\btablou unidimensional\b"), re.compile(r"\bvector(?:ul)?\b")),
    "matrices": (re.compile(r"\bmatrice\b"), re.compile(r"\btablou bidimensional\b")),
    "strings": (
        re.compile(r"\bsir(?:ul)? de caractere\b"),
        re.compile(r"\bcuv(?:a|i)nt(?:ul|e)?\b"),
        re.compile(r"\btext(?:ul)?\b"),
    ),
    "subprograms": (re.compile(r"\bsubprogram(?:ul|e)?\b"),),
    "recursion": (re.compile(r"\brecursiv"),),
    "graphs": (
        re.compile(r"\bgraf(?:ul|uri)?\b"),
        re.compile(r"\b(?:varfuri|arce|muchii)\b"),
    ),
    "trees": (
        re.compile(r"\barbore(?:le)?\b"),
        re.compile(r"\bradacina\b"),
        re.compile(r"\bvector(?:ul)? de tati\b"),
    ),
    "divisibility": (
        re.compile(r"\bdivizor(?:i|ii|ilor)?\b"),
        re.compile(r"\bnum(?:a|e)r prim\b"),
        re.compile(r"\bmultiplu\b"),
    ),
    "number processing": (
        re.compile(r"\bcifr(?:a|e|elor)?\b"),
        re.compile(r"\bnumar natural\b"),
    ),
    "combinatorics/backtracking": (
        re.compile(r"\bbacktracking\b"),
        re.compile(r"\bpermutar"),
        re.compile(r"\bcombinari\b"),
    ),
    "files": (
        re.compile(r"\bfisier(?:ul)?\b"),
        re.compile(r"\bbac\.(?:in|out|txt)\b"),
    ),
}


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def classify_topic(text: str) -> str:
    folded = _fold(text)
    matches = {
        topic
        for topic, patterns in _TOPIC_PATTERNS.items()
        if any(pattern.search(folded) for pattern in patterns)
    }
    if "trees" in matches and re.search(r"\bvector(?:ul)? de tati\b", folded):
        matches.discard("arrays")
    return next(iter(matches)) if len(matches) == 1 else "unclassified"


def classify_exercise_type(text: str) -> str:
    folded = _fold(text)
    if len(re.findall(r"\b[a-d]\.", folded)) >= 3:
        return "multiple_choice"
    if "pseudocod" in folded and re.search(r"\b[ab]\)", folded):
        return "pseudocode_analysis"
    if re.search(r"definitia completa a subprogramului", folded):
        return "subprogram_implementation"
    if re.search(r"scrie(?:ti)? programul", folded):
        return "program_implementation"
    return "open_response"

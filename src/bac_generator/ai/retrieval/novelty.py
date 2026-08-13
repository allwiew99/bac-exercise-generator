import re
import unicodedata

from pydantic import BaseModel, ConfigDict

from bac_generator.schemas.exercise import ExerciseResponse
from bac_generator.schemas.retrieval import RetrievedChunk

MIN_COPIED_TEST_INPUT_LENGTH = 4


class NoveltyPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    token_jaccard_threshold: float = 0.60
    shingle_containment_threshold: float = 0.60
    shingle_size: int = 5


DEFAULT_NOVELTY_POLICY = NoveltyPolicy()


class ReferenceSimilarity(BaseModel):
    reference_id: str
    normalized_exact_match: bool
    token_jaccard: float
    statement_shingle_containment: float
    solution_shingle_containment: float
    copied_constants: list[str]
    copied_test_case_count: int
    overall_similarity: float
    suspicious: bool


def normalize_for_similarity(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(re.findall(r"[^\W_]+", normalized, flags=re.UNICODE))


def evaluate_reference_similarity(
    exercise: ExerciseResponse,
    reference: RetrievedChunk,
    policy: NoveltyPolicy = DEFAULT_NOVELTY_POLICY,
) -> ReferenceSimilarity:
    statement = normalize_for_similarity(exercise.statement)
    solution = normalize_for_similarity(exercise.solution)
    reference_text = normalize_for_similarity(reference.text)

    token_jaccard = _token_jaccard(statement, reference_text)
    statement_shingle_containment = _shingle_containment(
        statement,
        reference_text,
        size=policy.shingle_size,
    )
    solution_shingle_containment = _shingle_containment(
        solution,
        reference_text,
        size=policy.shingle_size,
    )
    copied_constants = sorted(
        _constants(statement).intersection(_constants(reference_text))
    )
    copied_test_case_count = sum(
        _test_case_appears_in_reference(
            test_case.input,
            test_case.expected_output,
            reference_text,
        )
        for test_case in exercise.test_cases
    )
    normalized_exact_match = bool(statement) and statement == reference_text
    overall_similarity = max(
        token_jaccard,
        statement_shingle_containment,
        solution_shingle_containment,
    )
    suspicious = (
        normalized_exact_match
        or token_jaccard >= policy.token_jaccard_threshold
        or statement_shingle_containment
        >= policy.shingle_containment_threshold
    )

    return ReferenceSimilarity(
        reference_id=reference.id,
        normalized_exact_match=normalized_exact_match,
        token_jaccard=token_jaccard,
        statement_shingle_containment=statement_shingle_containment,
        solution_shingle_containment=solution_shingle_containment,
        copied_constants=copied_constants,
        copied_test_case_count=copied_test_case_count,
        overall_similarity=overall_similarity,
        suspicious=suspicious,
    )


def find_highest_reference_similarity(
    exercise: ExerciseResponse,
    references: list[RetrievedChunk],
    policy: NoveltyPolicy = DEFAULT_NOVELTY_POLICY,
) -> ReferenceSimilarity | None:
    if not references:
        return None

    results = [
        evaluate_reference_similarity(exercise, reference, policy)
        for reference in references
    ]
    return sorted(
        results,
        key=lambda result: (-result.overall_similarity, result.reference_id),
    )[0]


def _token_jaccard(left: str, right: str) -> float:
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    union = left_tokens.union(right_tokens)

    if not union:
        return 0.0

    return len(left_tokens.intersection(right_tokens)) / len(union)


def _shingle_containment(left: str, right: str, size: int) -> float:
    left_shingles = _shingles(left, size)
    right_shingles = _shingles(right, size)

    if not left_shingles or not right_shingles:
        return 0.0

    denominator = min(len(left_shingles), len(right_shingles))
    return len(left_shingles.intersection(right_shingles)) / denominator


def _shingles(text: str, size: int) -> set[tuple[str, ...]]:
    tokens = text.split()

    if len(tokens) < size:
        return set()

    return {
        tuple(tokens[index : index + size])
        for index in range(len(tokens) - size + 1)
    }


def _constants(text: str) -> set[str]:
    return set(re.findall(r"\b\d+(?:[.,]\d+)?\b", text))


def _test_case_appears_in_reference(
    test_input: str,
    expected_output: str,
    reference_text: str,
) -> bool:
    normalized_input = normalize_for_similarity(test_input)
    normalized_output = normalize_for_similarity(expected_output)

    return (
        len(normalized_input) >= MIN_COPIED_TEST_INPUT_LENGTH
        and bool(normalized_output)
        and normalized_input in reference_text
        and normalized_output in reference_text
    )

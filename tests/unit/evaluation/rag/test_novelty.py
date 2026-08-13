from bac_generator.evaluation.rag.novelty import (
    evaluate_reference_similarity,
    find_highest_reference_similarity,
    normalize_for_similarity,
)
from bac_generator.schemas.exercise import (
    Difficulty,
    ExerciseResponse,
    ExerciseTestCase,
)
from bac_generator.schemas.retrieval import RetrievedChunk


def _exercise(
    statement: str,
    *,
    solution: str = "int main() { return 0; }",
    test_input: str = "5\n1 2 3 4 5",
    expected_output: str = "15",
) -> ExerciseResponse:
    return ExerciseResponse(
        topic="arrays",
        difficulty=Difficulty.MEDIUM,
        statement=statement,
        solution=solution,
        explanation="Explicație.",
        test_cases=[
            ExerciseTestCase(
                input=test_input,
                expected_output=expected_output,
                is_hidden=False,
            )
        ],
    )


def _reference(reference_id: str, text: str) -> RetrievedChunk:
    return RetrievedChunk(
        id=reference_id,
        text=text,
        source="subject.pdf",
        topic="arrays",
        score=0.9,
    )


def test_similarity_normalization_preserves_words_and_romanian_diacritics() -> None:
    assert normalize_for_similarity("  Șirul,  are\n10 elemente! ") == (
        "șirul are 10 elemente"
    )


def test_identical_statement_is_flagged_as_suspicious() -> None:
    statement = "Se citește un vector cu n numere naturale distincte."

    result = evaluate_reference_similarity(
        _exercise(statement),
        _reference("ref-1", statement),
    )

    assert result.normalized_exact_match is True
    assert result.token_jaccard == 1.0
    assert result.statement_shingle_containment == 1.0
    assert result.suspicious is True


def test_near_copied_statement_has_high_shingle_containment() -> None:
    generated = (
        "Se citește un vector cu n numere naturale distincte și se cere suma lor."
    )
    reference = (
        "Se citește un vector cu n numere naturale distincte și se cere produsul lor."
    )

    result = evaluate_reference_similarity(
        _exercise(generated),
        _reference("ref-1", reference),
    )

    assert result.normalized_exact_match is False
    assert result.statement_shingle_containment == 0.8
    assert result.suspicious is True


def test_copied_test_case_is_reported_separately() -> None:
    result = evaluate_reference_similarity(
        _exercise(
            "Calculați o proprietate a vectorului.",
            test_input="5\n1 2 3 4 5",
            expected_output="15",
        ),
        _reference(
            "ref-1",
            "Exemplu: pentru datele 5 1 2 3 4 5 se afișează 15.",
        ),
    )

    assert result.copied_test_case_count == 1
    assert result.suspicious is False


def test_trivial_single_digit_test_case_does_not_trigger_copy_flag() -> None:
    result = evaluate_reference_similarity(
        _exercise(
            "Numărați cifrele unei valori.",
            test_input="0",
            expected_output="0",
        ),
        _reference(
            "ref-1",
            "Se citește n, unde n este mai mare sau egal cu 10.",
        ),
    )

    assert result.copied_test_case_count == 0
    assert result.suspicious is False


def test_highest_similarity_is_deterministic_for_reference_order() -> None:
    exercise = _exercise(
        "Determinați suma elementelor pare dintr-un vector de numere naturale."
    )
    references = [
        _reference("ref-z", "Determinați numărul de muchii ale unui graf."),
        _reference(
            "ref-a",
            "Determinați suma elementelor pare dintr-un vector de numere întregi.",
        ),
    ]

    forward = find_highest_reference_similarity(exercise, references)
    reverse = find_highest_reference_similarity(exercise, list(reversed(references)))

    assert forward is not None
    assert reverse is not None
    assert forward.reference_id == "ref-a"
    assert reverse.model_dump() == forward.model_dump()


def test_empty_reference_collection_has_no_highest_match() -> None:
    assert find_highest_reference_similarity(_exercise("Enunț nou."), []) is None

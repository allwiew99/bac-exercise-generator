import logging

import pytest

from bac_generator.ai.retrieval.novelty import (
    DEFAULT_NOVELTY_POLICY,
    ReferenceSimilarity,
)
from bac_generator.core.exceptions import ExerciseValidationError
from bac_generator.schemas.exercise import (
    Difficulty,
    ExerciseResponse,
    ExerciseTestCase,
)
from bac_generator.schemas.retrieval import RetrievedChunk
from bac_generator.services.exercise_novelty_validator import (
    ExerciseNoveltyValidator,
)


def _exercise(statement: str) -> ExerciseResponse:
    return ExerciseResponse(
        topic="pseudocode",
        difficulty=Difficulty.MEDIUM,
        statement=statement,
        solution="int main() { return 0; }",
        explanation="Explicație.",
        test_cases=[
            ExerciseTestCase(input="1", expected_output="1", is_hidden=False)
        ],
    )


def _reference(text: str = "reference-secret-text") -> RetrievedChunk:
    return RetrievedChunk(
        id="bac-reference-1",
        text=text,
        source="subject.pdf",
        topic="pseudocode",
        score=0.812345,
    )


def _similarity(
    *,
    exact: bool = False,
    token_jaccard: float = 0.0,
    shingle_containment: float = 0.0,
) -> ReferenceSimilarity:
    return ReferenceSimilarity(
        reference_id="bac-reference-1",
        normalized_exact_match=exact,
        token_jaccard=token_jaccard,
        statement_shingle_containment=shingle_containment,
        solution_shingle_containment=0.0,
        copied_constants=[],
        copied_test_case_count=0,
        overall_similarity=max(token_jaccard, shingle_containment),
        suspicious=False,
    )


def test_default_novelty_thresholds_are_centralized() -> None:
    assert DEFAULT_NOVELTY_POLICY.token_jaccard_threshold == 0.60
    assert DEFAULT_NOVELTY_POLICY.shingle_containment_threshold == 0.60
    assert DEFAULT_NOVELTY_POLICY.shingle_size == 5


@pytest.mark.parametrize(
    "similarity",
    [
        _similarity(exact=True),
        _similarity(token_jaccard=0.60),
        _similarity(shingle_containment=0.60),
    ],
)
def test_novelty_policy_rejects_exact_and_boundary_matches(
    similarity: ReferenceSimilarity,
) -> None:
    validator = ExerciseNoveltyValidator(
        similarity_evaluator=lambda _exercise, _reference: similarity
    )

    with pytest.raises(
        ExerciseValidationError,
        match="too similar.*bac-reference-1",
    ):
        validator.validate(_exercise("Enunț generat."), [_reference()])


def test_prior_pseudocode_copy_is_rejected_by_real_similarity() -> None:
    generated = (
        "Se consideră algoritmul alăturat, reprezentat în pseudocod. "
        "S-a notat cu a%b restul împărțirii numărului natural a la "
        "numărul natural nenul b. Scrieți valoarea afișată și două "
        "seturi de date de intrare."
    )
    reference = (
        "Se consideră algoritmul alăturat, reprezentat în pseudocod. "
        "S-a notat cu a%b restul împărțirii numărului natural a la "
        "numărul natural nenul b. Scrieți valoarea afișată și patru "
        "seturi de date de intrare."
    )

    with pytest.raises(ExerciseValidationError, match="too similar"):
        ExerciseNoveltyValidator().validate(
            _exercise(generated),
            [_reference(reference)],
        )


def test_shared_topic_vocabulary_is_not_rejected() -> None:
    ExerciseNoveltyValidator().validate(
        _exercise(
            "Determinați numărul valorilor prime dintr-un interval dat."
        ),
        [
            _reference(
                "Analizați pseudocodul care prelucrează cifrele unui număr "
                "natural și afișați suma cifrelor pare."
            )
        ],
    )


def test_novelty_logs_only_ids_and_scores(
    caplog: pytest.LogCaptureFixture,
) -> None:
    validator = ExerciseNoveltyValidator(
        similarity_evaluator=lambda _exercise, _reference: _similarity(
            token_jaccard=0.75
        )
    )

    with caplog.at_level(logging.WARNING), pytest.raises(
        ExerciseValidationError
    ):
        validator.validate(_exercise("generated-secret-text"), [_reference()])

    assert "bac-reference-1" in caplog.text
    assert "0.7500" in caplog.text
    assert "reference-secret-text" not in caplog.text
    assert "generated-secret-text" not in caplog.text


def test_novelty_evaluator_internal_failure_is_fail_open(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def failing_evaluator(
        _exercise: ExerciseResponse,
        _reference: RetrievedChunk,
    ) -> ReferenceSimilarity:
        raise RuntimeError("similarity implementation failed")

    validator = ExerciseNoveltyValidator(
        similarity_evaluator=failing_evaluator
    )

    with caplog.at_level(logging.WARNING):
        validator.validate(_exercise("Enunț generat."), [_reference()])

    assert "Novelty evaluation failed for reference id=bac-reference-1" in (
        caplog.text
    )
    assert "reference-secret-text" not in caplog.text

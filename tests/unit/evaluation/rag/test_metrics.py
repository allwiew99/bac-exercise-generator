import math

import pytest

from bac_generator.evaluation.rag.metrics import evaluate_ranking
from bac_generator.evaluation.rag.models import RelevanceGroup


def _group(
    group_id: str,
    grade: int,
    *document_ids: str,
) -> RelevanceGroup:
    return RelevanceGroup(
        id=group_id,
        grade=grade,
        document_ids=list(document_ids),
        rationale=f"Judgment for {group_id}",
    )


def test_metrics_use_relevance_groups_instead_of_duplicate_documents() -> None:
    groups = [
        _group("equivalent", 3, "mi-version", "sn-version"),
        _group("distinct", 2, "other-exercise"),
    ]

    metrics = evaluate_ranking(
        ["mi-version", "sn-version", "irrelevant", "other-exercise"],
        groups,
        cutoff=5,
    )

    ideal_dcg = 7.0 + 3.0 / math.log2(3.0)
    actual_dcg = 7.0 + 3.0 / math.log2(5.0)
    assert metrics.recall == 1.0
    assert metrics.mrr == 1.0
    assert metrics.ndcg == pytest.approx(actual_dcg / ideal_dcg)
    assert metrics.matched_group_ids == ["equivalent", "distinct"]
    assert metrics.raw_relevant_document_hits == 3
    assert metrics.duplicate_group_hits == 1


def test_metrics_respect_cutoff_and_first_relevant_rank() -> None:
    groups = [
        _group("first", 1, "relevant-one"),
        _group("second", 1, "relevant-two"),
    ]

    metrics = evaluate_ranking(
        ["irrelevant", "relevant-one", "relevant-two"],
        groups,
        cutoff=2,
    )

    assert metrics.recall == 0.5
    assert metrics.mrr == 0.5
    assert metrics.ndcg == pytest.approx(
        (1.0 / math.log2(3.0)) / (1.0 + 1.0 / math.log2(3.0))
    )
    assert metrics.matched_group_ids == ["first"]


def test_metrics_are_zero_when_no_relevance_group_is_retrieved() -> None:
    metrics = evaluate_ranking(
        ["irrelevant-a", "irrelevant-b"],
        [_group("relevant", 3, "target")],
        cutoff=5,
    )

    assert metrics.recall == 0.0
    assert metrics.mrr == 0.0
    assert metrics.ndcg == 0.0
    assert metrics.matched_group_ids == []
    assert metrics.raw_relevant_document_hits == 0
    assert metrics.duplicate_group_hits == 0


@pytest.mark.parametrize("cutoff", [0, -1])
def test_metrics_reject_non_positive_cutoffs(cutoff: int) -> None:
    with pytest.raises(ValueError, match="cutoff must be greater than zero"):
        evaluate_ranking([], [_group("relevant", 1, "target")], cutoff=cutoff)


def test_metrics_reject_document_ids_shared_by_multiple_groups() -> None:
    groups = [
        _group("first", 3, "shared"),
        _group("second", 2, "shared"),
    ]

    with pytest.raises(ValueError, match="shared.*multiple relevance groups"):
        evaluate_ranking(["shared"], groups, cutoff=5)

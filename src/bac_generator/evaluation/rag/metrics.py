import math

from bac_generator.evaluation.rag.models import (
    RankingMetrics,
    RelevanceGroup,
)


def evaluate_ranking(
    document_ids: list[str],
    relevance_groups: list[RelevanceGroup],
    cutoff: int,
) -> RankingMetrics:
    if cutoff <= 0:
        raise ValueError("cutoff must be greater than zero")

    group_by_document_id: dict[str, RelevanceGroup] = {}
    for group in relevance_groups:
        for document_id in group.document_ids:
            existing = group_by_document_id.get(document_id)
            if existing is not None and existing.id != group.id:
                raise ValueError(
                    f"Document ID {document_id!r} belongs to multiple relevance groups"
                )
            group_by_document_id[document_id] = group

    claimed_group_ids: set[str] = set()
    matched_group_ids: list[str] = []
    raw_relevant_document_hits = 0
    duplicate_group_hits = 0
    first_relevant_rank: int | None = None
    dcg = 0.0

    for rank, document_id in enumerate(document_ids[:cutoff], start=1):
        matched_group = group_by_document_id.get(document_id)
        if matched_group is None:
            continue

        raw_relevant_document_hits += 1
        if matched_group.id in claimed_group_ids:
            duplicate_group_hits += 1
            continue

        claimed_group_ids.add(matched_group.id)
        matched_group_ids.append(matched_group.id)
        if first_relevant_rank is None:
            first_relevant_rank = rank
        dcg += _gain(matched_group.grade) / math.log2(rank + 1)

    ideal_grades = sorted(
        (group.grade for group in relevance_groups),
        reverse=True,
    )[:cutoff]
    ideal_dcg = sum(
        _gain(grade) / math.log2(rank + 1)
        for rank, grade in enumerate(ideal_grades, start=1)
    )
    relevant_group_count = len(relevance_groups)

    return RankingMetrics(
        recall=(
            len(claimed_group_ids) / relevant_group_count
            if relevant_group_count
            else 0.0
        ),
        mrr=(1.0 / first_relevant_rank if first_relevant_rank is not None else 0.0),
        ndcg=(dcg / ideal_dcg if ideal_dcg else 0.0),
        matched_group_ids=matched_group_ids,
        relevant_groups=relevant_group_count,
        raw_relevant_document_hits=raw_relevant_document_hits,
        duplicate_group_hits=duplicate_group_hits,
    )


def _gain(grade: int) -> float:
    return float(2**grade - 1)

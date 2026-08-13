import logging
from collections.abc import Callable
from typing import Protocol

from bac_generator.ai.retrieval.novelty import (
    DEFAULT_NOVELTY_POLICY,
    NoveltyPolicy,
    ReferenceSimilarity,
    evaluate_reference_similarity,
)
from bac_generator.core.exceptions import ExerciseValidationError
from bac_generator.schemas.exercise import ExerciseResponse
from bac_generator.schemas.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

SimilarityEvaluator = Callable[
    [ExerciseResponse, RetrievedChunk],
    ReferenceSimilarity,
]


class ExerciseNoveltyValidatorProtocol(Protocol):
    def validate(
        self,
        exercise: ExerciseResponse,
        references: list[RetrievedChunk],
    ) -> None:
        ...


class ExerciseNoveltyValidator:
    def __init__(
        self,
        policy: NoveltyPolicy = DEFAULT_NOVELTY_POLICY,
        similarity_evaluator: SimilarityEvaluator = (
            evaluate_reference_similarity
        ),
    ) -> None:
        self.policy = policy
        self.similarity_evaluator = similarity_evaluator

    def validate(
        self,
        exercise: ExerciseResponse,
        references: list[RetrievedChunk],
    ) -> None:
        suspicious: list[ReferenceSimilarity] = []

        for reference in references:
            try:
                similarity = self.similarity_evaluator(exercise, reference)
            except Exception:
                logger.warning(
                    "Novelty evaluation failed for reference id=%s; "
                    "continuing without this comparison.",
                    reference.id,
                    exc_info=True,
                )
                continue

            if self._is_suspicious(similarity):
                suspicious.append(similarity)

        if not suspicious:
            return

        details = ", ".join(
            f"{result.reference_id} "
            f"(jaccard={result.token_jaccard:.4f}, "
            f"shingle={result.statement_shingle_containment:.4f}, "
            f"exact={result.normalized_exact_match})"
            for result in suspicious
        )
        logger.warning(
            "Generated statement rejected by novelty guard: references=%s",
            details,
        )
        raise ExerciseValidationError(
            "The generated statement is too similar to retrieved reference "
            f"material: {details}. Generate a genuinely different exercise "
            "with new wording, structure, constants, and examples."
        )

    def _is_suspicious(self, result: ReferenceSimilarity) -> bool:
        return (
            result.normalized_exact_match
            or result.token_jaccard
            >= self.policy.token_jaccard_threshold
            or result.statement_shingle_containment
            >= self.policy.shingle_containment_threshold
        )

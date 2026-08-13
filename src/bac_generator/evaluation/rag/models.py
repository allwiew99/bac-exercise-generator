from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvaluationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RelevanceGroup(EvaluationModel):
    id: str = Field(min_length=1)
    grade: int = Field(ge=1, le=3)
    document_ids: list[str] = Field(min_length=1)
    rationale: str = Field(min_length=1)

    @field_validator("id", "rationale")
    @classmethod
    def labels_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("document_ids")
    @classmethod
    def document_ids_must_be_unique(cls, value: list[str]) -> list[str]:
        stripped = [document_id.strip() for document_id in value]
        if any(not document_id for document_id in stripped):
            raise ValueError("document IDs must not be blank")
        if len(stripped) != len(set(stripped)):
            raise ValueError("document_ids must be unique within a relevance group")
        return stripped


class GoldenQuery(EvaluationModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    topic_filter: str | None = None
    relevance_groups: list[RelevanceGroup] = Field(min_length=1)

    @field_validator("id", "text", "topic")
    @classmethod
    def labels_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("topic_filter")
    @classmethod
    def optional_filter_must_not_be_blank(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class GoldenDataset(EvaluationModel):
    version: int = Field(ge=1)
    queries: list[GoldenQuery] = Field(min_length=1)


class RankingMetrics(EvaluationModel):
    recall: float = Field(ge=0.0, le=1.0)
    mrr: float = Field(ge=0.0, le=1.0)
    ndcg: float = Field(ge=0.0, le=1.0)
    matched_group_ids: list[str] = Field(default_factory=list)
    relevant_groups: int = Field(ge=0)
    raw_relevant_document_hits: int = Field(ge=0)
    duplicate_group_hits: int = Field(ge=0)


class RankedResult(EvaluationModel):
    rank: int = Field(ge=1)
    id: str = Field(min_length=1)
    score: float
    topic: str
    source: str
    year: int | None = None
    bac_section: str | None = None


QueryOutcome = Literal["improved", "unchanged", "degraded"]
FailureStage = Literal["retrieval", "reranking"]


class QueryEvaluation(EvaluationModel):
    query_id: str
    query_text: str
    topic: str
    topic_filter: str | None = None
    baseline_top8: list[RankedResult]
    baseline_top5: list[RankedResult]
    reranked_top5: list[RankedResult]
    baseline_at5: RankingMetrics
    baseline_at8: RankingMetrics
    reranked_at5: RankingMetrics
    outcome: QueryOutcome
    retrieval_latency_ms: float = Field(ge=0.0)
    reranker_latency_ms: float = Field(ge=0.0)
    combined_latency_ms: float = Field(ge=0.0)


class EvaluationFailure(EvaluationModel):
    query_id: str
    stage: FailureStage
    error_type: str
    message: str


class EvaluationRun(EvaluationModel):
    results: list[QueryEvaluation]
    failures: list[EvaluationFailure]


class MetricAggregate(EvaluationModel):
    recall_at5: float = Field(ge=0.0, le=1.0)
    mrr_at5: float = Field(ge=0.0, le=1.0)
    ndcg_at5: float = Field(ge=0.0, le=1.0)
    recall_at8: float | None = Field(default=None, ge=0.0, le=1.0)


class OutcomeCounts(EvaluationModel):
    improved: int = Field(ge=0)
    unchanged: int = Field(ge=0)
    degraded: int = Field(ge=0)


class LatencyStatistics(EvaluationModel):
    count: int = Field(ge=0)
    mean_ms: float = Field(ge=0.0)
    median_ms: float = Field(ge=0.0)
    p95_ms: float = Field(ge=0.0)
    min_ms: float = Field(ge=0.0)
    max_ms: float = Field(ge=0.0)


class LatencyAggregate(EvaluationModel):
    retrieval: LatencyStatistics
    reranker: LatencyStatistics
    combined: LatencyStatistics


class TopicEvaluationSummary(EvaluationModel):
    query_count: int = Field(ge=0)
    baseline: MetricAggregate
    reranked: MetricAggregate
    outcomes: OutcomeCounts


class EvaluationReport(EvaluationModel):
    generated_at: str
    reranker_model: str
    ranking_config: str
    total_queries: int = Field(ge=0)
    successful_queries: int = Field(ge=0)
    failed_queries: int = Field(ge=0)
    successful_query_ratio: float = Field(ge=0.0, le=1.0)
    failed_query_ratio: float = Field(ge=0.0, le=1.0)
    baseline: MetricAggregate
    reranked: MetricAggregate
    outcomes: OutcomeCounts
    latency: LatencyAggregate
    per_topic: dict[str, TopicEvaluationSummary]
    query_results: list[QueryEvaluation]
    failures: list[EvaluationFailure]

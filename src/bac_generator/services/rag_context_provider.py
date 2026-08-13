import logging
from collections.abc import Callable
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from bac_generator.schemas.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


class RagContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str = ""
    chunks: list[RetrievedChunk] = Field(default_factory=list)


class RetrievalServiceProtocol(Protocol):
    async def retrieve(
        self,
        query: str,
        topic: str | None = None,
        difficulty: str | None = None,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        ...


class RerankerProtocol(Protocol):
    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        ...


class ContextBuilderProtocol(Protocol):
    def build(
        self,
        chunks: list[RetrievedChunk],
        max_chunks: int = 5,
    ) -> str:
        ...


class RagContextProviderProtocol(Protocol):
    async def get_context(
        self,
        query: str,
        topic: str | None = None,
        difficulty: str | None = None,
    ) -> RagContext:
        ...


RetrievalServiceFactory = Callable[[], RetrievalServiceProtocol]
RerankerFactory = Callable[[], RerankerProtocol]


class RagContextProvider:
    def __init__(
        self,
        retrieval_service_factory: RetrievalServiceFactory,
        reranker_factory: RerankerFactory | None,
        context_builder: ContextBuilderProtocol,
        *,
        rag_enabled: bool,
        reranker_enabled: bool,
        rag_fail_open: bool,
        context_top_k: int = 5,
    ) -> None:
        if context_top_k <= 0:
            raise ValueError("context_top_k must be greater than zero")

        self.retrieval_service_factory = retrieval_service_factory
        self.reranker_factory = reranker_factory
        self.context_builder = context_builder
        self.rag_enabled = rag_enabled
        self.reranker_enabled = reranker_enabled
        self.rag_fail_open = rag_fail_open
        self.context_top_k = context_top_k

    async def get_context(
        self,
        query: str,
        topic: str | None = None,
        difficulty: str | None = None,
    ) -> RagContext:
        if not self.rag_enabled:
            return RagContext()

        try:
            retrieval_service = self.retrieval_service_factory()
            chunks = await retrieval_service.retrieve(
                query=query,
                topic=topic,
                difficulty=difficulty,
            )
            context_chunks = chunks

            if self.reranker_enabled:
                if self.reranker_factory is None:
                    raise RuntimeError(
                        "reranker_factory must be configured when reranking is enabled"
                    )
                reranker = self.reranker_factory()
                context_chunks = await reranker.rerank(
                    query=query,
                    chunks=chunks,
                )

            context = self.context_builder.build(
                context_chunks,
                max_chunks=self.context_top_k,
            )

            logger.info(
                "RAG context succeeded: retrieved=%d, context_candidates=%d, "
                "reranker_enabled=%s.",
                len(chunks),
                len(context_chunks),
                self.reranker_enabled,
            )
            return RagContext(
                text=context,
                chunks=context_chunks,
            )

        except Exception:
            if not self.rag_fail_open:
                raise

            logger.warning(
                "RAG context failed. Falling back to generation without "
                "retrieval context.",
                exc_info=True,
            )
            return RagContext()

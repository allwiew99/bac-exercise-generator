import asyncio
import logging

from bac_generator.ai.embeddings.embedding_client import EmbeddingClient
from bac_generator.repositories.vector_repository_protocol import (
    VectorRepositoryProtocol,
)
from bac_generator.schemas.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(
        self,
        embedding_client: EmbeddingClient,
        vector_repository: VectorRepositoryProtocol,
        default_top_k: int = 8,
    ) -> None:
        self.embedding_client = embedding_client
        self.vector_repository = vector_repository
        self.default_top_k = default_top_k

    async def retrieve(
        self,
        query: str,
        topic: str | None = None,
        difficulty: str | None = None,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        query = query.strip()

        if not query:
            raise ValueError("Retrieval query cannot be empty.")

        effective_top_k = self.default_top_k if top_k is None else top_k

        if effective_top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        filters: dict[str, str | int] = {}

        if topic:
            filters["topic"] = topic

        if difficulty:
            filters["difficulty"] = difficulty

        logger.info(
            "Retrieving RAG context for query='%s', topic='%s', "
            "difficulty='%s', top_k=%d.",
            query,
            topic,
            difficulty,
            effective_top_k,
        )

        query_vector = await asyncio.to_thread(
            self.embedding_client.embed_text,
            query,
        )

        chunks = await asyncio.to_thread(
            self.vector_repository.query,
            query_vector,
            effective_top_k,
            filters or None,
        )

        if filters and len(chunks) < effective_top_k:
            logger.warning(
                "Filtered RAG retrieval returned %d/%d candidates; "
                "falling back to semantic retrieval without metadata filters.",
                len(chunks),
                effective_top_k,
            )

            semantic_chunks = await asyncio.to_thread(
                self.vector_repository.query,
                query_vector,
                effective_top_k,
                None,
            )
            chunks = self._merge_chunks(
                chunks,
                semantic_chunks,
                effective_top_k,
            )

        logger.info(
            "Retrieved %d RAG chunks.",
            len(chunks),
        )

        return chunks[:effective_top_k]

    @staticmethod
    def _merge_chunks(
        filtered_chunks: list[RetrievedChunk],
        semantic_chunks: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        chunks_by_id: dict[str, RetrievedChunk] = {}

        for chunk in (*filtered_chunks, *semantic_chunks):
            existing = chunks_by_id.get(chunk.id)
            if existing is None or chunk.score > existing.score:
                chunks_by_id[chunk.id] = chunk

        return sorted(
            chunks_by_id.values(),
            key=lambda chunk: chunk.score,
            reverse=True,
        )[:top_k]

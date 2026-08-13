import asyncio
import logging

from bac_generator.ai.embeddings.embedding_client import EmbeddingClient
from bac_generator.repositories.vector_repository_protocol import (
    VectorMetadata,
    VectorRepositoryProtocol,
)
from bac_generator.schemas.retrieval import RetrievalDocument

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(
        self,
        embedding_client: EmbeddingClient,
        vector_repository: VectorRepositoryProtocol,
        batch_size: int = 32,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero.")

        self.embedding_client = embedding_client
        self.vector_repository = vector_repository
        self.batch_size = batch_size

    async def ingest(
        self,
        documents: list[RetrievalDocument],
    ) -> int:
        if not documents:
            logger.info("No documents provided for ingestion.")
            return 0

        self._validate_unique_ids(documents)

        total_ingested = 0

        for start in range(0, len(documents), self.batch_size):
            batch = documents[start : start + self.batch_size]

            texts = [document.text for document in batch]

            embeddings = await asyncio.to_thread(
                self.embedding_client.embed_texts,
                texts,
            )

            if len(embeddings) != len(batch):
                raise RuntimeError(
                    "Embedding count does not match document count."
                )

            vectors = [
                (
                    document.id,
                    embedding,
                    self._build_metadata(document),
                )
                for document, embedding in zip(
                    batch,
                    embeddings,
                    strict=True,
                )
            ]

            await asyncio.to_thread(
                self.vector_repository.upsert,
                vectors,
            )

            total_ingested += len(batch)

            logger.info(
                "Ingested RAG batch with %d documents. Total=%d.",
                len(batch),
                total_ingested,
            )

        logger.info(
            "RAG ingestion completed successfully. Total documents=%d.",
            total_ingested,
        )

        return total_ingested

    @staticmethod
    def _build_metadata(
        document: RetrievalDocument,
    ) -> VectorMetadata:
        metadata: VectorMetadata = {
            "text": document.text,
            "source": document.source,
            "topic": document.topic,
            "language": document.language,
        }

        if document.year is not None:
            metadata["year"] = document.year

        if document.bac_section is not None:
            metadata["bac_section"] = document.bac_section

        if document.exercise_type is not None:
            metadata["exercise_type"] = document.exercise_type

        if document.difficulty is not None:
            metadata["difficulty"] = document.difficulty

        return metadata

    @staticmethod
    def _validate_unique_ids(
        documents: list[RetrievalDocument],
    ) -> None:
        ids = [document.id for document in documents]

        if len(ids) != len(set(ids)):
            raise ValueError(
                "Retrieval documents must have unique IDs."
            )
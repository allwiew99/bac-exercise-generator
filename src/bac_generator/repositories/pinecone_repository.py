from pinecone import Pinecone

from bac_generator.core.config import settings
from bac_generator.schemas.retrieval import RetrievedChunk


class PineconeRepository:
    def __init__(self) -> None:
        self._client = Pinecone(
            api_key=settings.pinecone_api_key,
        )

        self._index = self._client.Index(
            settings.pinecone_index_name,
        )

    def query(
        self,
        vector: list[float],
        top_k: int,
        filters: dict[str, str | int] | None = None,
    ) -> list[RetrievedChunk]:
        response = self._index.query(
            vector=vector,
            top_k=top_k,
            filter=filters,
            include_metadata=True,
            namespace=settings.pinecone_namespace,
        )

        chunks: list[RetrievedChunk] = []

        for match in response.matches:
            metadata = match.metadata or {}

            chunks.append(
                RetrievedChunk(
                    id=match.id,
                    text=str(metadata.get("text", "")),
                    source=str(metadata.get("source", "")),
                    topic=str(metadata.get("topic", "")),
                    year=(
                        int(metadata["year"])
                        if metadata.get("year") is not None
                        else None
                    ),
                    bac_section=(
                        str(metadata["bac_section"])
                        if metadata.get("bac_section") is not None
                        else None
                    ),
                    exercise_type=(
                        str(metadata["exercise_type"])
                        if metadata.get("exercise_type") is not None
                        else None
                    ),
                    difficulty=(
                        str(metadata["difficulty"])
                        if metadata.get("difficulty") is not None
                        else None
                    ),
                    score=float(match.score or 0.0),
                )
            )

        return chunks

    def upsert(
        self,
        vectors: list[
            tuple[
                str,
                list[float],
                dict[str, str | int | float | bool],
            ]
        ],
    ) -> None:
        self._index.upsert(
            vectors=vectors,
            namespace=settings.pinecone_namespace,
        )

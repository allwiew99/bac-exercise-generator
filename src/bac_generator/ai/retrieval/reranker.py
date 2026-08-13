import asyncio
import logging

from google.cloud import discoveryengine_v1 as discoveryengine

from bac_generator.core.config import settings
from bac_generator.schemas.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


class Reranker:
    def __init__(
        self,
        project_id: str,
        model: str = "semantic-ranker-default@latest",
        top_n: int = 5,
    ) -> None:
        if not project_id:
            raise ValueError("project_id must be configured.")

        if top_n <= 0:
            raise ValueError("top_n must be greater than zero.")

        self.project_id = project_id
        self.model = model
        self.top_n = top_n
        self._client = discoveryengine.RankServiceClient()

        self._ranking_config = self._client.ranking_config_path(
            project=project_id,
            location="global",
            ranking_config="default_ranking_config",
        )

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        if not chunks:
            return []

        if not settings.reranker_enabled:
            return chunks[: self.top_n]

        return await asyncio.to_thread(
            self._rerank_sync,
            query,
            chunks,
        )

    def _rerank_sync(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        records = [
            discoveryengine.RankingRecord(
                id=chunk.id,
                title=self._build_title(chunk),
                content=chunk.text,
            )
            for chunk in chunks
        ]

        request = discoveryengine.RankRequest(
            ranking_config=self._ranking_config,
            model=self.model,
            top_n=min(self.top_n, len(records)),
            query=query,
            records=records,
        )

        response = self._client.rank(
            request=request,
        )

        chunks_by_id = {
            chunk.id: chunk
            for chunk in chunks
        }

        reranked: list[RetrievedChunk] = []

        for record in response.records:
            chunk = chunks_by_id.get(record.id)

            if chunk is None:
                continue

            reranked.append(
                chunk.model_copy(
                    update={
                        "score": float(record.score),
                    }
                )
            )

        logger.info(
            "Reranked %d retrieved chunks into %d results.",
            len(chunks),
            len(reranked),
        )

        return reranked

    @staticmethod
    def _build_title(
        chunk: RetrievedChunk,
    ) -> str:
        parts = [
            chunk.topic,
        ]

        if chunk.difficulty:
            parts.append(chunk.difficulty)

        if chunk.year is not None:
            parts.append(str(chunk.year))

        if chunk.bac_section:
            parts.append(chunk.bac_section)

        return " | ".join(parts)
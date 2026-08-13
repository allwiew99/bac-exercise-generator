import asyncio
import json
from pathlib import Path

from pydantic import TypeAdapter

from bac_generator.ai.embeddings.vertex_embedding_client import (
    VertexEmbeddingClient,
)
from bac_generator.repositories.pinecone_repository import (
    PineconeRepository,
)
from bac_generator.schemas.retrieval import RetrievalDocument
from bac_generator.services.ingestion_service import IngestionService

CORPUS_PATH = Path("data/rag/bac_corpus.json")


def load_documents() -> list[RetrievalDocument]:
    if not CORPUS_PATH.exists():
        raise FileNotFoundError(
            f"Corpus file not found: {CORPUS_PATH}"
        )

    raw_data = json.loads(
        CORPUS_PATH.read_text(encoding="utf-8")
    )

    adapter = TypeAdapter(
        list[RetrievalDocument]
    )

    return adapter.validate_python(raw_data)


async def main() -> None:
    documents = load_documents()

    if not documents:
        print("Corpus is empty. Nothing to ingest.")
        return

    embedding_client = VertexEmbeddingClient()
    vector_repository = PineconeRepository()

    service = IngestionService(
        embedding_client=embedding_client,
        vector_repository=vector_repository,
    )

    total = await service.ingest(documents)

    print(
        f"Successfully ingested {total} documents into Pinecone."
    )


if __name__ == "__main__":
    asyncio.run(main())
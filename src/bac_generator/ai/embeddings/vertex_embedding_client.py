from google import genai
from google.genai import types

from bac_generator.ai.embeddings.embedding_client import EmbeddingClient
from bac_generator.core.config import settings


class VertexEmbeddingClient(EmbeddingClient):
    def __init__(self) -> None:
        self._client = genai.Client(
            vertexai=True,
            project=settings.gemini_project,
            location=settings.gemini_location,
        )

    def embed_text(self, text: str) -> list[float]:
        response = self._client.models.embed_content(
            model=settings.embedding_model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=settings.embedding_dimensions,
            ),
        )

        if not response.embeddings:
            raise RuntimeError("Embedding response did not contain embeddings.")

        embedding = response.embeddings[0]

        if embedding.values is None:
            raise RuntimeError("Embedding response did not contain values.")

        return list(embedding.values)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []

        for text in texts:
            response = self._client.models.embed_content(
                model=settings.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=settings.embedding_dimensions,
                ),
            )

            if not response.embeddings:
                raise RuntimeError(
                    "Embedding response did not contain embeddings."
                )

            embedding = response.embeddings[0]

            if embedding.values is None:
                raise RuntimeError(
                    "Embedding response did not contain values."
                )

            embeddings.append(list(embedding.values))

        return embeddings
from unittest.mock import Mock, patch

from bac_generator.ai.embeddings.vertex_embedding_client import VertexEmbeddingClient
from bac_generator.core.config import settings
from bac_generator.repositories.pinecone_repository import PineconeRepository
from bac_generator.services.rate_limiter import RedisRateLimiter


@patch("bac_generator.ai.embeddings.vertex_embedding_client.genai.Client")
def test_vertex_client_configures_request_timeout(client_factory: Mock) -> None:
    VertexEmbeddingClient()

    http_options = client_factory.call_args.kwargs["http_options"]
    assert http_options.timeout == settings.embedding_timeout_seconds * 1000


@patch("bac_generator.repositories.pinecone_repository.Pinecone")
def test_pinecone_client_configures_request_timeout(client_factory: Mock) -> None:
    PineconeRepository()

    assert client_factory.call_args.kwargs["timeout"] == (
        settings.pinecone_timeout_seconds
    )


@patch("bac_generator.services.rate_limiter.Redis")
def test_redis_client_configures_request_timeout(redis_factory: Mock) -> None:
    RedisRateLimiter(host="redis.internal")

    assert redis_factory.call_args.kwargs["socket_connect_timeout"] == (
        settings.redis_timeout_seconds
    )
    assert redis_factory.call_args.kwargs["socket_timeout"] == (
        settings.redis_timeout_seconds
    )

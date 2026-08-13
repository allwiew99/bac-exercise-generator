from pinecone import Pinecone, ServerlessSpec

from bac_generator.core.config import settings


def main() -> None:
    if not settings.pinecone_api_key:
        raise ValueError("PINECONE_API_KEY is not configured.")

    if not settings.pinecone_index_name:
        raise ValueError("PINECONE_INDEX_NAME is not configured.")

    client = Pinecone(
        api_key=settings.pinecone_api_key,
    )

    if client.has_index(settings.pinecone_index_name):
        print(
            f"Index '{settings.pinecone_index_name}' already exists."
        )
        return

    client.create_index(
        name=settings.pinecone_index_name,
        vector_type="dense",
        dimension=settings.embedding_dimensions,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1",
        ),
        deletion_protection="disabled",
        tags={
            "application": "bac-exercise-generator",
            "purpose": "rag",
        },
    )

    print(
        f"Created Pinecone index "
        f"'{settings.pinecone_index_name}'."
    )


if __name__ == "__main__":
    main()
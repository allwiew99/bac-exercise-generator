from typing import Protocol

from bac_generator.schemas.retrieval import RetrievedChunk

VectorMetadata = dict[str, str | int | float | bool]


class VectorRepositoryProtocol(Protocol):
    def query(
        self,
        vector: list[float],
        top_k: int,
        filters: dict[str, str | int] | None = None,
    ) -> list[RetrievedChunk]:
        ...

    def upsert(
        self,
        vectors: list[
            tuple[
                str,
                list[float],
                VectorMetadata,
            ]
        ],
    ) -> None:
        ...

from pathlib import Path

from bac_generator.evaluation.rag.models import GoldenDataset
from bac_generator.schemas.retrieval import RetrievalDocument


def load_golden_dataset(
    path: Path,
    corpus_documents: list[RetrievalDocument],
) -> GoldenDataset:
    dataset = GoldenDataset.model_validate_json(path.read_text(encoding="utf-8"))
    corpus_ids = {document.id for document in corpus_documents}
    query_ids: set[str] = set()
    relevant_document_ids: set[str] = set()

    for query in dataset.queries:
        if query.id in query_ids:
            raise ValueError(f"Duplicate query ID: {query.id}")
        query_ids.add(query.id)

        group_ids: set[str] = set()
        group_by_document_id: dict[str, str] = {}

        for group in query.relevance_groups:
            if group.id in group_ids:
                raise ValueError(
                    f"Duplicate relevance group ID {group.id!r} in query {query.id!r}"
                )
            group_ids.add(group.id)

            for document_id in group.document_ids:
                existing_group_id = group_by_document_id.get(document_id)
                if existing_group_id is not None:
                    raise ValueError(
                        f"Document ID {document_id!r} belongs to multiple relevance "
                        f"groups in query {query.id!r}: {existing_group_id!r} and "
                        f"{group.id!r}"
                    )
                group_by_document_id[document_id] = group.id
                relevant_document_ids.add(document_id)

    unknown_ids = sorted(relevant_document_ids - corpus_ids)
    if unknown_ids:
        raise ValueError(
            "Unknown relevant document IDs: " + ", ".join(unknown_ids)
        )

    return dataset

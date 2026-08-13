import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from bac_generator.evaluation.rag.dataset import load_golden_dataset
from bac_generator.schemas.retrieval import RetrievalDocument


def _corpus_document(document_id: str) -> RetrievalDocument:
    return RetrievalDocument(
        id=document_id,
        text=f"Exercise {document_id}",
        source="subject.pdf",
        topic="arrays",
    )


def _dataset_payload() -> dict[str, Any]:
    return {
        "version": 1,
        "queries": [
            {
                "id": "arrays-binary-search",
                "text": "Exercițiu de căutare binară.",
                "topic": "binary search",
                "topic_filter": "arrays",
                "relevance_groups": [
                    {
                        "id": "same-exercise",
                        "grade": 3,
                        "document_ids": ["mi-document", "sn-document"],
                        "rationale": "Equivalent MI and SN variants.",
                    }
                ],
            }
        ],
    }


def _write_payload(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "golden.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_golden_dataset_accepts_known_transparent_group_ids(
    tmp_path: Path,
) -> None:
    path = _write_payload(tmp_path, _dataset_payload())

    dataset = load_golden_dataset(
        path,
        [_corpus_document("mi-document"), _corpus_document("sn-document")],
    )

    assert dataset.queries[0].id == "arrays-binary-search"
    assert dataset.queries[0].relevance_groups[0].document_ids == [
        "mi-document",
        "sn-document",
    ]


def test_load_golden_dataset_rejects_unknown_relevant_document_ids(
    tmp_path: Path,
) -> None:
    path = _write_payload(tmp_path, _dataset_payload())

    with pytest.raises(
        ValueError,
        match="Unknown relevant document IDs.*sn-document",
    ):
        load_golden_dataset(path, [_corpus_document("mi-document")])


def test_load_golden_dataset_rejects_duplicate_query_ids(tmp_path: Path) -> None:
    payload = _dataset_payload()
    payload["queries"].append(dict(payload["queries"][0]))
    path = _write_payload(tmp_path, payload)

    with pytest.raises(ValueError, match="Duplicate query ID.*arrays-binary-search"):
        load_golden_dataset(
            path,
            [_corpus_document("mi-document"), _corpus_document("sn-document")],
        )


def test_load_golden_dataset_rejects_duplicate_group_ids(tmp_path: Path) -> None:
    payload = _dataset_payload()
    group = dict(payload["queries"][0]["relevance_groups"][0])
    group["document_ids"] = ["other-document"]
    payload["queries"][0]["relevance_groups"].append(group)
    path = _write_payload(tmp_path, payload)

    with pytest.raises(ValueError, match="Duplicate relevance group ID.*same-exercise"):
        load_golden_dataset(
            path,
            [
                _corpus_document("mi-document"),
                _corpus_document("sn-document"),
                _corpus_document("other-document"),
            ],
        )


def test_load_golden_dataset_rejects_document_in_multiple_groups(
    tmp_path: Path,
) -> None:
    payload = _dataset_payload()
    payload["queries"][0]["relevance_groups"].append(
        {
            "id": "different-exercise",
            "grade": 2,
            "document_ids": ["sn-document"],
            "rationale": "This accidental overlap is invalid.",
        }
    )
    path = _write_payload(tmp_path, payload)

    with pytest.raises(
        ValueError,
        match="sn-document.*multiple relevance groups",
    ):
        load_golden_dataset(
            path,
            [_corpus_document("mi-document"), _corpus_document("sn-document")],
        )


def test_load_golden_dataset_rejects_whitespace_only_labels(tmp_path: Path) -> None:
    payload = _dataset_payload()
    payload["queries"][0]["text"] = "   "
    path = _write_payload(tmp_path, payload)

    with pytest.raises(ValidationError, match="must not be blank"):
        load_golden_dataset(
            path,
            [_corpus_document("mi-document"), _corpus_document("sn-document")],
        )

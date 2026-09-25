import json
from pathlib import Path

import pytest

from bac_generator.evaluation.generation_quality import load_generation_cases


def test_committed_generation_dataset_has_30_unique_representative_cases() -> None:
    cases = load_generation_cases(
        Path("data/rag/evaluation/generation_quality_cases.json")
    )

    assert len(cases) == 30
    assert len({case.id for case in cases}) == 30
    assert {case.difficulty.value for case in cases} == {"easy", "medium", "hard"}
    assert len({case.topic for case in cases}) >= 10


def test_generation_dataset_rejects_too_few_cases(tmp_path: Path) -> None:
    path = tmp_path / "cases.json"
    path.write_text(
        json.dumps([{"id": "one", "topic": "arrays", "difficulty": "easy"}]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="at least 30"):
        load_generation_cases(path)

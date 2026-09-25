from pathlib import Path

from pydantic import RootModel

from bac_generator.evaluation.rag.generation_e2e import GenerationCase


class GenerationDataset(RootModel[list[GenerationCase]]):
    pass


def load_generation_cases(path: Path) -> list[GenerationCase]:
    dataset = GenerationDataset.model_validate_json(
        path.read_text(encoding="utf-8")
    ).root
    if len(dataset) < 30:
        raise ValueError("Generation evaluation requires at least 30 cases.")
    case_ids = [case.id for case in dataset]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Generation evaluation case ids must be unique.")
    return dataset

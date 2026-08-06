from pathlib import Path

from pytest import MonkeyPatch

from bac_generator.core.config import Settings


def test_settings_defaults(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    settings = Settings()

    assert settings.app_name == "Bac Exercise Generator API"
    assert settings.debug is False
    assert settings.database_url == (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/bac_generator"
    )
    assert settings.llm_max_attempts == 3

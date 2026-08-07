from pathlib import Path

from pytest import MonkeyPatch

from bac_generator.core.config import Settings


def test_settings_defaults(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_PROJECT", raising=False)
    monkeypatch.delenv("GEMINI_LOCATION", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    settings = Settings()

    assert settings.app_name == "Bac Exercise Generator API"
    assert settings.debug is False
    assert settings.database_url == (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/bac_generator"
    )
    assert settings.llm_max_attempts == 3
    assert settings.llm_provider == "ollama"
    assert settings.gemini_project == ""
    assert settings.gemini_location == "us-central1"
    assert settings.gemini_model == "gemini-2.5-flash"

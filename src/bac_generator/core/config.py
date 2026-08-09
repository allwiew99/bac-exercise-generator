from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Bac Exercise Generator API"
    debug: bool = False

    cors_origins: str = "http://localhost:3000"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:9b"

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/bac_generator"
    )

    llm_max_attempts: int = 3
    llm_provider: str = "ollama"

    code_runner_provider: str = "local"

    firebase_project_id: str = ""

    gemini_project: str = ""
    gemini_location: str = "us-central1"
    gemini_model: str = "gemini-2.5-flash"

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
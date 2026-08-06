from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Bac Exercise Generator API"
    debug: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:9b"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/bac_generator"


settings = Settings()

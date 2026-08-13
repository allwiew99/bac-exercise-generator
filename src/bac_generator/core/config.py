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

    llm_max_attempts: int = 6
    llm_provider: str = "ollama"

    code_runner_provider: str = "local"

    rate_limiter_provider: str = "memory"
    redis_host: str = ""
    redis_port: int = 6379

    firebase_project_id: str = ""

    gemini_project: str = ""
    gemini_location: str = "us-central1"
    gemini_model: str = "gemini-2.5-flash"
    gemini_max_output_tokens: int = 8192

    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 768

    pinecone_api_key: str = ""
    pinecone_index_name: str = ""
    pinecone_namespace: str = "bac-exercises"

    rag_enabled: bool = True
    rag_fail_open: bool = True

    reranker_enabled: bool = False
    reranker_model: str = "semantic-ranker-default@latest"
    reranker_top_n: int = 5

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()

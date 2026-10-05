from typing import Literal
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from JOBMIND_* environment variables or .env file."""

    service_name: str = "JobMind"
    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # LLM
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 2

    # Embeddings
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_vector_size: int = 1536   # Size for text-embedding-3-small

    # RAG chunking
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Qdrant — ":memory:" for local dev; provide URL for production
    qdrant_url: str = ":memory:"
    qdrant_collection: str = "jobmind_docs"

    # Candidate preferences and short-lived conversation context
    database_url: str | None = None
    redis_url: str | None = None
    session_ttl_seconds: int = Field(default=86400, ge=60)
    session_max_messages: int = Field(default=30, ge=2, le=200)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="JOBMIND_",
        extra="ignore",
    )

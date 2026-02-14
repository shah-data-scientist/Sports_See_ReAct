"""
FILE: config.py
STATUS: Active
RESPONSIBILITY: Pydantic Settings configuration with validation for all app settings
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation.

    All settings are loaded from environment variables or .env file.
    Validation ensures type safety and required values are present.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    mistral_api_key: str = Field(
        ...,
        description="Mistral AI API key (required)",
        min_length=10,
    )
    google_api_key: str | None = Field(
        default=None,
        description="Google API key for Gemini (used by RAGAS evaluator)",
    )

    # Model Configuration
    embedding_model: str = Field(
        default="mistral-embed",
        description="Model for generating embeddings",
    )
    chat_model: str = Field(
        default="gemini-2.0-flash",
        description="Model for chat completion (Gemini 2.0 Flash for best accuracy on SQL data)",
        alias="MODEL_NAME",
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="LLM temperature (0=deterministic, 2=creative)",
    )

    # Chunking Configuration
    chunk_size: int = Field(
        default=1500,
        ge=100,
        le=10000,
        description="Document chunk size in characters",
    )
    chunk_overlap: int = Field(
        default=150,
        ge=0,
        le=1000,
        description="Overlap between chunks in characters",
    )
    embedding_batch_size: int = Field(
        default=32,
        ge=1,
        le=100,
        description="Batch size for embedding API calls",
    )

    # Search Configuration
    search_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of documents to retrieve",
    )
    min_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score (0-1) for results",
    )

    # Paths (relative to project root, consolidated under data/)
    input_dir: str = Field(default="data/inputs")
    vector_db_dir: str = Field(default="data/vector")
    database_dir: str = Field(default="data/sql")

    # Application
    app_title: str = Field(default="NBA Analyst AI")
    app_name: str = Field(default="NBA", alias="NAME")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_cors_origins: list[str] = Field(default=["*"])

    # Rate Limiting
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_window: int = Field(default=60, ge=1, description="Window in seconds")

    # Security
    max_query_length: int = Field(
        default=2000,
        ge=10,
        le=10000,
        description="Maximum allowed query length",
    )

    # Observability
    logfire_token: str | None = Field(default=None, description="Logfire API token (requires project:write scope)")
    logfire_enabled: bool = Field(default=True, description="Enable Logfire tracing (auto-disabled if token missing)")

    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap(cls, v: int, info) -> int:
        """Ensure overlap is less than chunk size."""
        chunk_size = info.data.get("chunk_size", 1500)
        if v >= chunk_size:
            raise ValueError(f"chunk_overlap ({v}) must be less than chunk_size ({chunk_size})")
        return v

    @property
    def faiss_index_path(self) -> Path:
        """Path to FAISS index file."""
        return Path(self.vector_db_dir) / "faiss_index.idx"

    @property
    def document_chunks_path(self) -> Path:
        """Path to document chunks pickle file."""
        return Path(self.vector_db_dir) / "document_chunks.pkl"

    @property
    def database_path(self) -> Path:
        """Path to SQLite database."""
        return Path(self.database_dir) / "interactions.db"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Validated Settings instance

    Raises:
        ValidationError: If required settings are missing or invalid
    """
    return Settings()


# Global settings instance
settings = get_settings()

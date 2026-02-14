"""
FILE: models.py
STATUS: Active
RESPONSIBILITY: Pydantic models for each data pipeline stage (load, clean, chunk, embed, index)
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class LoadStageInput(BaseModel):
    """Input for the document loading stage."""

    input_dir: str = Field(min_length=1, description="Directory containing source documents")
    data_url: str | None = Field(default=None, description="Optional download URL")

    @field_validator("input_dir")
    @classmethod
    def validate_no_traversal(cls, v: str) -> str:
        """Block path traversal attempts."""
        if ".." in v:
            raise ValueError("Path traversal not allowed in input_dir")
        return v


class RawDocument(BaseModel):
    """A raw document from the loading stage."""

    page_content: str = Field(min_length=1, description="Extracted text content")
    metadata: dict[str, str | int | float] = Field(default_factory=dict)


class LoadStageOutput(BaseModel):
    """Output from the document loading stage."""

    documents: list[RawDocument]
    document_count: int = Field(ge=0)
    errors: list[str] = Field(default_factory=list)


class CleanedDocument(BaseModel):
    """A document after text cleaning and validation."""

    page_content: str = Field(min_length=1, description="Cleaned text content")
    metadata: dict[str, str | int | float] = Field(default_factory=dict)
    char_count: int = Field(ge=1, description="Character count of cleaned content")


class CleanStageOutput(BaseModel):
    """Output from the text cleaning stage."""

    documents: list[CleanedDocument]
    removed_count: int = Field(ge=0, description="Documents removed during cleaning")
    total_chars: int = Field(ge=0, description="Total characters across all documents")


class ChunkData(BaseModel):
    """A single text chunk with metadata.

    Attributes:
        id: Unique chunk identifier
        text: Chunk text content
        metadata: Chunk metadata including data_type tag for filtering
    """

    id: str = Field(min_length=1, description="Unique chunk identifier")
    text: str = Field(min_length=1, description="Chunk text content")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Chunk metadata including data_type tag",
    )


class ChunkStageOutput(BaseModel):
    """Output from the chunking stage."""

    chunks: list[ChunkData]
    chunk_count: int = Field(ge=0)


class QualityCheckResult(BaseModel):
    """Result from LLM-powered quality validation of a chunk."""

    chunk_id: str
    is_coherent: bool = Field(description="Whether the chunk is coherent and readable")
    quality_score: float = Field(ge=0.0, le=1.0, description="Quality score 0-1")
    issues: list[str] = Field(default_factory=list, description="Quality issues found")


class EmbedStageOutput(BaseModel):
    """Output metadata from the embedding stage."""

    embedding_count: int = Field(ge=0)
    embedding_dimension: int = Field(ge=1)


class IndexStageOutput(BaseModel):
    """Output from the index building stage."""

    index_size: int = Field(ge=0, description="Number of vectors in the index")
    index_path: str = Field(description="Path to the FAISS index file")
    chunks_path: str = Field(description="Path to the chunks pickle file")


class PipelineResult(BaseModel):
    """Complete pipeline execution summary."""

    documents_loaded: int = Field(ge=0)
    documents_cleaned: int = Field(ge=0)
    chunks_created: int = Field(ge=0)
    embeddings_generated: int = Field(ge=0)
    index_size: int = Field(ge=0)
    quality_checks_passed: int | None = None
    quality_checks_total: int | None = None
    processing_time_ms: float = Field(ge=0.0)
    errors: list[str] = Field(default_factory=list)
